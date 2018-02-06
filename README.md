# IPEDS-API
A python script to automate fetching data from the IPEDS database by scrapping its website

It has been tested to work with python2. 

# Usage (with College Affordability Group Website)
1. Run `python data_script.py <with options, see section below>` to download all the csv files you want to import into the database

2. Run `python generator.py` to generate `model.py` and `admin.py` that Django uses to create the database scheme (`model.py`) and to register the database in the admin interface (`admin.py`)

3. Run `python manage.py makemigrations --empty` (from the root) to create deafult empty migrations

4. Run `python manage.py makemigrations` to make the initial migrations 

5. Copy `migrate_data.py` into the migrations folder and modify the second option of the `dependcies` line to the name of the inital migration file created during step 4

    > dependencies = [
        ('ipeds_import', '< filename before .py of initial migration file created in step 4 >')
    ]

6. Now everything should be ready to go! Run `python manage.py runserver` to start the server and head to `localhost:8000/admin` to log in and see the changes made to the database


# Usage (with just data_script.py)
usage: data_script.py [-h] [-f] [-p PREFIX] [-y YEAR] [-s SERIES SERIES]
                      [-c CHECK] [-a] [-d]

This program scraps the IPEDS website for its .csv data files.

optional arguments:

  -h, --help            show this help message and exit

  -f, --fresh           refreshes download cache, run if the files you are
                        getting are old
  
  -p PREFIX, --prefix PREFIX
                        define the prefix of the files wanted, default is "HD"
                        (for getting HDxxxx.zip files for example)
  
  -y YEAR, --year YEAR  input one number indicating the year you want and
                        downloads it with specified prefix
  
  -s SERIES SERIES, --series SERIES SERIES
                        input two numbers indicating series of years you want
                        (from year of first number to year of second number)
                        and downloads them with specified prefix
  
  -c CHECK, --check CHECK
                        checks to see if the files (with the given prefix -
                        default is HD - and year) exist
  
  -a, --checkAll        checks to see if any files exist (note that checkAll
                        overrides all other options), <Response 200> indicates
                        that it does (google search HTTP codes for other
                        troubleshooting)
  
  -d, --downloadAll     downloads all files with specified prefix
