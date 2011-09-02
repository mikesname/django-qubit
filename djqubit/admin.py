"""
Admin config for Qubit models.  This is not going to be comprehensive.
"""
from django.contrib import admin
from models import InformationObject, Event

admin.site.register(InformationObject)
admin.site.register(Event)
