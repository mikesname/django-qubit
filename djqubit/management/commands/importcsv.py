"""
Import a csv file or files into the database.
"""

import os
import csv
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

from djqubit import models

HELP = """Import CSV files into the database.  The CSV file should have
a header row with headings in the format <ModelName__childmodel_field>.
i.e: Repository__i18n_authorised_form_of_name.
Child models are assumed to always be a (not-previously-existing) one-to-
many related object, i.e: a note or contact information.""" 

class Command(BaseCommand):
    args = "<csvfile>"
    help = HELP
    option_list = BaseCommand.option_list + (
        make_option(
            "-l",
            "--lang",
            action="store",
            dest="lang",
            default="en",
            help="Language for imported i18n fields"),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("One (and only one) CSV file must be provided")


