"""
Admin config for Qubit models.  This is not going to be comprehensive.
"""
from django.contrib import admin
from models import InformationObject, Event, Actor, Repository, Term, Taxonomy,\
        User, Note, DigitalObject, Relation        

admin.site.register(InformationObject)
admin.site.register(Event)
admin.site.register(Actor)
admin.site.register(Repository)
admin.site.register(Term)
admin.site.register(Taxonomy)
admin.site.register(User)
admin.site.register(Note)
admin.site.register(DigitalObject)
admin.site.register(Relation)
