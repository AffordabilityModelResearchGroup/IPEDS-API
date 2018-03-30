""" script to scrap IPEDS website for .csv files """
import argparse
import zipfile
import shutil
import glob
import re
import requests
import os
import errno

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.common.keys import Keys


def scrape(output_file='./cache/ipeds_data.html'):
    """ get html page that lists its links to .zip files """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    # https://nces.ed.gov/ipeds/datacenter/Default.aspx?gotoReportId=7&fromIpeds=true
    driver.get('https://nces.ed.gov/ipeds/datacenter/login.aspx?gotoReportId=7')

    driver.implicitly_wait(10)
    button = driver.find_element_by_id('ImageButton1')
    button.click()
    driver.implicitly_wait(10)
    button = driver.find_element_by_id('contentPlaceHolder_ibtnContinue')
    button.click()

    if not os.path.exists(os.path.dirname(output_file)):
        try:
            os.makedirs(os.path.dirname(output_file))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(output_file, 'w') as out_file:
        out_file.write(driver.page_source.encode('utf-8'))
    driver.close()


def get_dlinks(ipeds_data_file='./cache/ipeds_data.html', dlinks_file='./cache/download_links.txt'):
    """ parses html for download links """
    # input everything in HTML file into html_doc for processing
    with open(ipeds_data_file) as in_file:
        html_doc = str(in_file.readlines())

    # initialize BeautifulSoup parser for html_doc
    soup = BeautifulSoup(html_doc, 'html.parser')

    # filter html_doc for data we want
    with open(dlinks_file, 'w') as out_file:
        # find all anchor tags with href property = 'data'
        for line in soup.find_all(href=re.compile("data")):
            # convert working line into string for easier processing
            line = str(line)
            # find the index the ends the substring "<a href=\""
            index_begin = line.find('<a href=\"') + len('<a href=\"')
            # find the index the ends the substring ".zip"
            index_end = line.find('.zip') + len('.zip')
            # filer line down "data/<filename>.zip" (ex. "data/HD2015.zip")
            line = line[index_begin : index_end]
            # filter out empty lines
            if line == '':
                continue
            else:
                # write the partial url ("data/<filename>.zip") into file
                out_file.write("{}\n".format(line))


def unzip_delete(filename):
    """ unzips zip files and deletes zip file, take in filename without file extension """
    # unzip zip files
    with zipfile.ZipFile('./data/{}'.format(filename),"r") as zip_ref:
        zip_ref.extractall('./csv/{}'.format(filename))
    
    # zipfile unzips files but keeps the directory structure
    # i.e. file.zip becomse file.zip > fileCSV.csv
    # these next two pieces of code:
    
    # move csv file out of folder
    for unzipped_file in glob.glob('./csv/{}/*'.format(filename)):
        shutil.move(unzipped_file, './csv/')
    
    # delete (now) empty folder
    shutil.rmtree('./csv/{}'.format(filename))


def single_download(year, check=False, prefix='HD', url='data/', file_ex='.zip'):
    """ downloads a single year's .zip data file """
    if check is True:
        # checks if file exists
        res = requests.head('https://nces.ed.gov/ipeds/datacenter/{}{}{}{}'
                        .format(url, prefix, year, file_ex))
        print('{}{}{} {}'.format(prefix, year, file_ex, str(res)))
    else:
        res = requests.get('https://nces.ed.gov/ipeds/datacenter/{}{}{}{}'
                        .format(url, prefix, year, file_ex))
        if res.status_code == 200:
            with open('./data/{}{}.zip'.format(prefix, year), 'wb') as out_file:
                out_file.write(res.content)
            unzip_delete('{}{}'.format(prefix, year))
            return 0
        else:
            return -1


def series_download(year_begin, year_end, prefix='HD', url='data/', file_ex='.zip'): 
    """ downloads all .zip data files from the year_begin to year_end """
    if (year_begin > year_end):
        tmp = year_begin
        year_begin = year_end
        year_end = tmp

    for year in range(year_begin, year_end + 1):
        print('Downloading {}{} File'.format(prefix, year))
        single_download(year, prefix='HD', url='data/', file_ex='.zip')
        print('...Download {}{} File Complete'.format(prefix, year))


def downloader(prefix='HD', check_all=False):
    """ parses file (download_links.txt) generates by g_dlinks()
    and downloads (or checks) .zip files """
    # download wanted files
    with open('./cache/download_links.txt') as in_file:
        for line in in_file:
            line = str(line)
            line = line.strip()
            filename = os.path.split(line)[1]

            if check_all is True:
                # checks if any file exists
                res = requests.head('https://nces.ed.gov/ipeds/datacenter/{}'.format(line))
                print(line + ' ' + str(res))
            elif not filename.startswith(prefix):
                # skip the current line if not the prefix we want
                continue
            else:
                # download file
                res = requests.get('https://nces.ed.gov/ipeds/datacenter/{}'.format(line))
                if res.status_code == 200:
                    with open('./data/{}'.format(filename),
                              'wb') as out_file:
                        out_file.write(res.content)
                    print('...Download {} Complete'.format(filename))
                    unzip_delete('{}'.format(filename))
                else:
                    print(str(res.headers))
                    # skip the current line
                    continue


def main():
    """ main subroutine """
    des = """This program scraps the IPEDS website for its .csv data files."""

    # initiate the parser
    parser = argparse.ArgumentParser(description=des)
    year_group = parser.add_mutually_exclusive_group()
    # define argument options
    parser.add_argument('-f',
                        '--fresh',
                        help='refreshes download cache, \
                        run if the files you are getting are old',
                        action='store_true')
    parser.add_argument('-p',
                        '--prefix',
                        help='define the prefix of the files wanted, \
                        default is "HD" (for getting HDxxxx.zip files for example)')
    year_group.add_argument('-y',
                        '--year',
                        help='input one number indicating the year you want \
                        and downloads it with specified prefix')
    year_group.add_argument('-s',
                        '--series',
                        nargs=2,
                        help='input two numbers indicating series of years you want \
                        (from year of first number to year of second number) \
                        and downloads them with specified prefix')
    parser.add_argument('-c',
                        '--check',
                        help='checks to see if the files \
                        (with the given prefix - default is HD - and year) exist')
    parser.add_argument('-a',
                        '--checkAll',
                        help='checks to see if any files exist \
                        (note that checkAll overrides all other options), \
                        <Response 200> indicates that it does \
                        (google search HTTP codes for other troubleshooting)',
                        action='store_true')
    parser.add_argument('-d',
                        '--downloadAll',
                        help='downloads all files with specified prefix',
                        action='store_true')

    # read arguments from the command line
    args = parser.parse_args()

    print('')
    if args.checkAll:
        print('Checking All Files...')
        downloader(check_all=True)
        return

    if args.fresh:
        print('Refreshing Download Cache...')
        scrape()
        print('...Parsing HTML for Download Links...')
        get_dlinks()
        print('...Download Cache Refreshed')
        return

    if args.prefix is None:
        args.prefix = 'HD'
    print('Prefix Used: {}'.format(args.prefix))

    if args.check:
        print('Checking {}{} File'.format(args.prefix, args.check))
        single_download(args.check, prefix='HD', check=True)
        return
    
    if args.year:
        print('Year: {}'.format(args.year))
        print('Downloading {}{} File'.format(args.prefix, args.year))
        if single_download(args.year, prefix=args.prefix) == 0:
            print('...Download Complete')
        else:
            print('...File Does Not Exist')
        return
    
    if args.series:
        print('Years: {} - {}'.format(args.series[0], args.series[1]))
        series_download(int(args.series[0]), int(args.series[1]))
        return

    if args.downloadAll:
        print('Downloading All {} Files...'.format(args.prefix))
        downloader(prefix=args.prefix)
        print('...Download Complete')


if __name__ == '__main__':
    main()
