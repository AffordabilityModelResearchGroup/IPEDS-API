from subprocess import call
import os

# print(os.path.dirname(os.path.abspath(__file__)))
# print(os.path.dirname(os.path.abspath()))

os.chdir(os.path.dirname(os.path.abspath(__file__)))

call('python ./IPEDS-API/data_script.py -d'.split(' '))
call('python generator.py')