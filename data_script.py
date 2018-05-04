""" script to scrap IPEDS website for .csv files """
import argparse
import zipfile
import shutil
import glob
import re
import requests
import os
import errno
import pandas

from bs4 import BeautifulSoup

from selenium import webdriver
from sqlalchemy import create_engine
from sqlalchemy.types import String, BigInteger
from sqlalchemy.exc import NoSuchTableError
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
        link_set = set()
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
            if line == '' or \
                    "Stata" in line or \
                    "SPS" in line or \
                    "Dict" in line or \
                    "SAS" in line:
                continue
            else:
                # write the partial url ("data/<filename>.zip") into file
                link_set.add(line)

        for link in link_set:
            out_file.write("{}\n".format(link))


def unzip_delete(zip_filename):
    """ unzips zip files and deletes zip file, take in filename without file extension """
    # unzip zip files
    with zipfile.ZipFile('./data/{}'.format(zip_filename), "r") as zip_ref:
        zip_ref.extractall('./csv/{}'.format(zip_filename))
    
    # zipfile unzips files but keeps the directory structure
    # i.e. file.zip becomse file.zip > fileCSV.csv
    # these next two pieces of code:
    
    # move csv file out of folder
    for unzipped_file in glob.glob('./csv/{}/*'.format(zip_filename)):
        filename = os.path.split(unzipped_file)[1]
        shutil.move(unzipped_file, os.path.join('./csv/', filename))
    
    # delete (now) empty folder
    shutil.rmtree('./csv/{}'.format(zip_filename))

# TODO: update to include suffix
# def single_check(year, prefix, url='data/', file_ex='.zip'):
#     # checks if file exists
#     res = requests.head('https://nces.ed.gov/ipeds/datacenter/{}{}{}{}'
#                     .format(url, prefix, year, file_ex))
#     print('{}{}{} {}'.format(prefix, year, file_ex, str(res)))

# TODO: update to include suffix
# def single_download(year, prefix, url='data/', file_ex='.zip'):
#     """ downloads a single year's .zip data file """
#     res = requests.get('https://nces.ed.gov/ipeds/datacenter/{}{}{}{}'
#                     .format(url, prefix, year, file_ex))
#     if res.status_code == 200:
#         with open('./data/{}{}.zip'.format(prefix, year), 'wb') as out_file:
#             out_file.write(res.content)
#         unzip_delete('{}{}'.format(prefix, year))
#         return 0
#     else:
#         return -1

# TODO: update to include suffix
# def series_download(year_begin, year_end, prefix, url='data/', file_ex='.zip'): 
#     """ downloads all .zip data files from the year_begin to year_end """
#     if (year_begin > year_end):
#         tmp = year_begin
#         year_begin = year_end
#         year_end = tmp

#     for year in range(year_begin, year_end + 1):
#         print('Downloading {}{} File'.format(prefix, year))
#         single_download(year, prefix='HD', url='data/', file_ex='.zip')
#         print('...Download {}{} File Complete'.format(prefix, year))


def checker():
    with open('./cache/download_links.txt') as in_file:
        for line in in_file:
            line = str(line)
            line = line.strip()
            # checks if any file exists
            res = requests.head('https://nces.ed.gov/ipeds/datacenter/{}'.format(line))
            print(line + ' ' + str(res))


def downloader(prefix, suffix, year_begin, check_all=False ):
    """ parses file (download_links.txt) generates by g_dlinks()
    and downloads (or checks) .zip files """

    # we need to pad suffix with '_' to match file names
    # i.e. file is name ic2000_ay.csv so pad a suffix, 'AY', with '_'
    if (suffix != ''):
        suffix = '_' + suffix
        # make sure its uppercase when refering to zip
        suffix = suffix.upper()

    # regex expression to match files we want
    match = re.compile('{0}\d{{4,4}}{1}.zip'.format(prefix.upper(), suffix.upper()))
    year_matcher = re.compile("\d{4,4}")

    with open('./cache/download_links.txt') as in_file:
        for line in in_file:
            line = str(line).strip()
            filename = os.path.split(line)[1]
            if match.search(filename) and \
                (
                    int(year_matcher.search(filename).group()) >= 2007 or 
                    int(year_matcher.search(filename).group()[2:]) >= 7
                ):
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


def process_csv(prefix, suffix, copy_to_database=True):
    prefix = prefix.lower()
    sql_engine = create_engine('postgresql://aff:123456@localhost:5432/affordability_model')

    # # drop the existing table
    # meta = MetaData(sql_engine)
    # try:
    #     ipeds_table = Table('IPEDS', meta, autoload=True)
    #     ipeds_table.drop(sql_engine)
    # except NoSuchTableError:
    #     pass

    # we need to pad suffix with '_' to match file names
    # i.e. file is name ic2000_ay.csv so pad a suffix, 'AY', with '_'
    if (suffix != ''):
        suffix = '_' + suffix
        # make sure its lowercase when refering to csv
        suffix = suffix.lower()

    # Process each csv file
    view_name = prefix + suffix
    sql_engine.execute("drop view if exists " + view_name + ";")
    create_view_statement = "CREATE OR REPLACE VIEW public." + view_name + " AS "
    common_column_statement = ""

    for file_path in sorted(glob.glob("./csv/{}*{}.csv".format(prefix, suffix)), reverse=True):
        if not re.compile("./csv/{}\d{{4,4}}{}.csv".format(prefix, suffix)).match(file_path):
            continue
        # IPEDS seems to use a western encoding instead of UTF-8
        csv = pandas.read_csv(file_path, encoding="windows-1252")
        # convert column names to lowercase
        for column in csv.columns:
            csv.rename(columns={column:column.strip("\"").strip().lower()}, inplace=True)
        # utility: parses file_path i.e. ./csv/hd2016.csv > hd2016.csv
        file_name = os.path.basename(file_path)
        # utility: get only file_name i.e. hd2016.csv > hd2016
        file_name_no_ext, extension = os.path.splitext(file_name)
        file_name_no_ext = file_name_no_ext.lower()
        # logging
        print("...Processing " + file_name_no_ext)
        # strip out prefix, leaving only year i.e. hd2016 > 2016
        # year = file_name_no_ext.lower().strip(prefix.lower())
        year = file_name_no_ext.lower().strip(prefix.lower()).strip(suffix.lower()).strip('_').strip('_rv')
        # add a year column
        csv["year"] = int(year)
        # logging?
        csv.to_csv("last_processed.csv", encoding='utf-8')

        # this if contains the SQL statements to create tables and import data
        if copy_to_database:
            # this create tables and import data into the database
            csv.to_sql(name=file_name_no_ext, con=sql_engine, if_exists="replace", index=False, dtype={"unitid": BigInteger})
            # these makes the unified view of all IPEDS data in our database
            common_column_statement += "select column_name, data_type from information_schema.columns" \
                                        " where table_name = '{}' intersect ".format(file_name_no_ext.strip())
            # {{0}} so that {0} survives
            create_view_statement += "select {{0}} from {} union ".format(file_name_no_ext)

    # cleanup, cuts off one comma
    common_column_statement = common_column_statement[:-len("intersect")-1]
    create_view_statement = create_view_statement[:-len("union")-1]
    # create a string of all column names 
    common_column_names = ", ".join([i[0] for i in list(sql_engine.execute(common_column_statement))])
    # part of the code that executes the SQL to make the unified view
    # {0} from earlier gets formatted here
    sql_engine.execute(create_view_statement.format(common_column_names))

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
    parser.add_argument('-pp',
                        '--suffix',
                        help='define the suffix of the files wanted, \
                        default is "" (nothing) \
                        (ex. HDxxxx_AY.zip would be retrieved if given default prefix and \'AY\' suffix)')
    parser.add_argument('-y',
                        '--year',
                        help='define the year to limit files to ones after the specified year, \
                        default is "2007" \
                        (ex. HD2007.zip and HD2008.zip would be retrieved, HD2006.zip would not)')
    # TODO: -y option stolen by another function, rename option
    # year_group.add_argument('-y',
    #                     '--year',
    #                     help='input one number indicating the year you want \
    #                     and downloads it with specified prefix')
    # year_group.add_argument('-s',
    #                     '--series',
    #                     nargs=2,
    #                     help='input two numbers indicating series of years you want \
    #                     (from year of first number to year of second number) \
    #                     and downloads them with specified prefix')
    # parser.add_argument('-c',
    #                     '--check',
    #                     help='checks to see if the file with the given year \
    #                     (and given prefix, default is HD unless defined with -p) exist')
    parser.add_argument('--checkAll',
                        help='checks to see if any files exist \
                        (note that checkAll overrides all other options), \
                        <Response 200> indicates that it does \
                        (google search HTTP codes for other troubleshooting)',
                        action='store_true')
    parser.add_argument('-d',
                        '--downloadAll',
                        help='downloads all files with specified prefix',
                        action='store_true')
    parser.add_argument('--proc',
                        help='imports data into our postgres database \
                        (this also runs after all downloading functions; \
                        its main purpose is for reruning processing when/if it fails',
                        action='store_true')

    # read arguments from the command line
    args = parser.parse_args()

    print('')
    if args.checkAll:
        print('Checking All Files...')
        checker()
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

    if args.suffix is None:
        args.suffix = ''
    print('Suffix Used: {}'.format(args.suffix))

    if args.year is None:
        args.year = '2007'
    print('Restricting Files to Years On and After: {}'.format(args.year))

    # TODO: update to include suffix
    # if args.check:
    #     print('Checking {}{} File'.format(args.prefix, args.check))
    #     # single_download(args.check, prefix='HD', check=True)
    #     single_check(args.check, prefix='HD')
    #     return
    
    # TODO: update to include suffix
    # if args.year:
    #     print('Year: {}'.format(args.year))
    #     print('Downloading {}{} File'.format(args.prefix, args.year))
    #     if single_download(args.year, prefix=args.prefix) == 0:
    #         # process_csv()
    #         print('...Download Complete')
    #     else:
    #         print('...File Does Not Exist')
    #     return
    
    # TODO: update to include suffix
    # if args.series:
    #     print('Years: {} - {}'.format(args.series[0], args.series[1]))
    #     series_download(int(args.series[0]), int(args.series[1]), prefix=args.prefix)
    #     # process_csv()
    #     return

    if args.downloadAll:
        print('Downloading All {} Files...'.format(args.prefix))
        downloader(prefix=args.prefix, suffix=args.suffix, year_begin=args.year)
        process_csv(prefix=args.prefix, suffix=args.suffix)
        print('...Download Complete')

    if args.proc:
        print('csv Processing...')
        process_csv(args.prefix, args.suffix)
        print('...csv Processing Complete')


if __name__ == '__main__':
    main()
