"""
Admin config for Qubit models.  This is not going to be comprehensive.
"""
from django.contrib import admin
from models import InformationObject, Event, Actor, Repository, Term, Taxonomy

admin.site.register(InformationObject)
admin.site.register(Event)
admin.site.register(Actor)
admin.site.register(Repository)
admin.site.register(Term)
admin.site.register(Taxonomy)
