from subprocess import call
import os
import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
now = datetime.datetime.now()
end_year = now.year
start_year = end_year - 5
call('python ./IPEDS-API/data_script.py -s {} {}'.format(start_year, end_year).split(' '))
call('python generator.py')