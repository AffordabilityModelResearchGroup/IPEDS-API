from django.contrib import admin
from ipeds_import.model import *

# Register your models here.
class hd2013_admin(admin.ModelAdmin):
    pass

admin.site.register(hd2013_model, hd2013_admin)

class hd2014_admin(admin.ModelAdmin):
    pass

admin.site.register(hd2014_model, hd2014_admin)

class hd2015_admin(admin.ModelAdmin):
    pass

admin.site.register(hd2015_model, hd2015_admin)

class hd2016_admin(admin.ModelAdmin):
    pass

admin.site.register(hd2016_model, hd2016_admin)

