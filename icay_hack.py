import glob
import re
import os
def process_csv(prefix, suffix):
    prefix = prefix.lower()
    # we need to pad suffix with '_' to match file names
    # i.e. file is name ic2000_ay.csv so pad a suffix, 'AY', with '_'
    if (suffix != ''):
        suffix = '_' + suffix
        # make sure its lowercase when refering to csv
        suffix = suffix.lower()

    for file_path in sorted(glob.glob("./csv/{}*{}.csv".format(prefix, suffix)), reverse=True):
        # if not re.compile("./csv/{}\d{{4,4}}{}.csv".format(prefix, suffix)).match(file_path):
        #     continue
        with(open(file_path)) as infile:
            file_name = os.path.basename(file_path)
            print(file_name)
            with(open('./safe_ic_ay/{}'.format(file_name), 'w+')) as outfile:
                for line in infile:
                    if line.find('UNITID') != -1:
                        outfile.write(line)
                        continue
                    else:
                        outfile.write('id:{}{}'.format(line[:line.find(',')], line[line.find(','):]))

def main():
    process_csv('ic', 'ay')

if __name__ == '__main__':
    main()