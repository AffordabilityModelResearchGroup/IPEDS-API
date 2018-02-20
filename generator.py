import os
import csv

print('\n')

def generate_base_names():
    with open('./base_names.txt', 'w') as base_names:
        files = os.listdir('./csv')
        files = [x for x in files if x.find('.csv') != -1]
        for f in files:
            filename = f[ : f.find('.csv')]
            base_names.write('{}\n'.format(filename))


def generate_admin():
    with open('./base_names.txt') as base_names:
        with open('./output/admin.py', 'w') as admin:
            admin.write('from django.contrib import admin\n')
            admin.write('from ipeds_import.model import *\n\n')
            admin.write('# Register your models here.\n')
            for name in base_names:
                name = name.strip()
                admin.write('class {}_admin(admin.ModelAdmin):\n'.format(name))
                admin.write('    pass\n\n')
                admin.write('admin.site.register({}_model, {}_admin)\n\n'.format(name, name))

def generate_model():
    with open('./base_names.txt') as base_names:
        with open('./output/model.py', 'w') as model:
            model.write('from django.db import models\n\n')
            model.write('# auto generated model classes from csv file\n')
            for name in base_names:
                name = name.strip()
                # filename = f[ : f.find('.csv')]
                model.write('class {}_model(models.Model):\n'.format(name))
                with open('./csv/{}.csv'.format(name)) as csvfile:
                    fields = str(csvfile.readline()).strip().split(',')
                    for field in fields:
                        model.write('    {} = models.CharField(max_length=255, default=\'null\')\n'.format(field))
                model.write('\n')

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Generating base_names.txt...")
    generate_base_names()
    print("Generating model.py...")
    generate_model()
    print("Generating admin.py...")
    generate_admin()
    print("...Finished!")

if __name__ == '__main__':
    main()
    