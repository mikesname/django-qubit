"""
Import a csv file or files into the database.
  fields are:
    Address
    City
    Contact
    Country        
    E-mail
    English Name
    Extra
    Fax
    Origin
    Original Name
    Phone
    Source
    State
    Survey 1
    URL

"""

import csv
from optparse import make_option
import exceptions
import phpserialize

from incf.countryutils import data as countrydata

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.exceptions import ImproperlyConfigured
from django.template.defaultfilters import slugify

from djqubit import models

HELP = """Import CSV files into the database.""" 


class CvsImportError(CommandError):
    pass


class Command(BaseCommand):
    args = "<csvfile>"
    help = HELP
    option_list = BaseCommand.option_list + (
        make_option(
            "-f",
            "--from",
            action="store",
            dest="fromrec",
            type="int",
            default=1,
            help="Import records from this offset"),
        make_option(
            "-t",
            "--to",
            action="store",
            dest="to",
            type="int",
            default=-1,
            help="Import records up to this offset"),
        make_option(
            "-u",
            "--user",
            action="store",
            dest="user",
            default="qubit",
            help="User to own imported records"),
        make_option(
            "-l",
            "--lang",
            action="store",
            dest="lang",
            default="en",
            help="Language for imported i18n fields"),
    )

    @transaction.commit_manually
    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("One (and only one) CSV file must be provided")

        # attempt to sniff the CSV dialect
        handle = open(args[0], "rb")
        sample = handle.read(1024)
        handle.seek(0)        
        dialect = csv.Sniffer().sniff(sample)

        user = models.User.objects.get(username=options["user"])
        status = models.Term.objects.get(
                taxonomy=models.Taxonomy.DESCRIPTION_STATUS_ID,
                i18n__name__exact="Draft")
        detail = models.Term.objects.get(
                taxonomy=models.Taxonomy.DESCRIPTION_DETAIL_LEVEL_ID,
                i18n__name__exact="Partial")

        # the first line MUST be headers
        reader = csv.DictReader(handle, dialect=dialect)
        try:
            for record in reader:
                if options["fromrec"] > 0 and reader.line_num < options["fromrec"]:
                    continue
                self.stdout.write("Adding %d: %s\n" % (reader.line_num, record["Original Name"]))
                self.handle_row(record, reader.line_num, options["lang"], user, status, detail)
                if options["to"] > 0 and reader.line_num == options["to"]:
                    break
        except exceptions.BaseException, err:
            self.stderr.write("Caught exception: %s, Rolling back imports...\n" % err)
            transaction.rollback()
            raise err
        else:
            transaction.commit()
        handle.close()                    

    def handle_row(self, rawrecord, index, lang, user, status, detail):
        record = {}
        for k, v in rawrecord.iteritems():
            if isinstance(v, str):
                record[k] = unicode(v, encoding="utf8")
            else:
                record[k] = unicode("", encoding="utf8")

        countrycode = self._get_country_code(record)
        ident = "ehri%d%s" % (index, countrycode)
        truncname = record["Original Name"][0:255]
        repo = models.Repository(
            identifier=ident,
            entity_type_id=models.Term.CORPORATE_BODY_ID,
            source_culture=lang,
            repository_source_culture=lang,
            parent_id=models.Actor.ROOT_ID,
            description_status=status,
            description_detail=detail,
            desc_status=status,
            desc_detail=detail
        )
        repo.save()
        repo.base_actor.set_i18n(lang, dict(
            authorized_form_of_name=truncname,
            desc_sources=record["Origin"]
        ))

        slug = models.Slug(
            object_id=repo,
            slug=self.unique_slug(truncname, models.Slug)
        )
        slug.save()        

        if record["Comments"].strip():
            comment = models.Note(
                    object_id=repo,
                    type_id=models.Term.MAINTENANCE_NOTE_ID,
                    user=user,
                    source_culture=lang,
                    scope="QubitRepository")
            comment.save()
            comment.set_i18n(lang, dict(
                    content=record["Comments"],
            ))

        if record["Extra"].strip():
            extra = models.Note(
                    object_id=repo,
                    type_id=models.Term.MAINTENANCE_NOTE_ID,
                    user=user,
                    source_culture=lang,
                    scope="QubitRepository")
            extra.save()
            extra.set_i18n(lang, dict(
                    content=record["Extra"],
            ))

        if record["English Name"].strip():
            othername = models.OtherName(
                    object_id=repo,
                    type_id=models.Term.OTHER_FORM_OF_NAME_ID,
                    source_culture=lang)
            othername.save()
            othername.set_i18n(lang, dict(
                name=record["English Name"].strip()[0:255]
            ))

        contact = models.ContactInformation(
            actor=repo,
            primary_contact=True,
            contact_person=record["Contact"],
            country_code=countrycode,
            email=record["E-mail"],
            website=record["URL"],
            street_address=self._get_address(record),
            fax=record["Fax"],
            telephone=record["Phone"])
        contact.save()
        contact.set_i18n(lang, dict(
                contact_type="Main",
                city=record["City"],
                region=record["State"],
                note="Import from EHRI contact spreadsheet"
        ))

        langprop = models.Property(
                object_id=repo,
                name="language",
                source_culture=lang
        )
        langprop.save()
        langprop.set_i18n(lang, dict(
            value=phpserialize.dumps([lang])
        ))
        scriptprop = models.Property(
                object_id=repo,
                name="script",
                source_culture=lang
        )
        scriptprop.save()
        scriptprop.set_i18n(lang, dict(
            value=phpserialize.dumps(["Latn"])
        ))

            


    def _get_country_code(self, record):
        ccn = countrydata.cn_to_ccn.get(record["Country"].strip())
        if ccn is None:
            return
        return countrydata.ccn_to_cca2.get(ccn)

    def _get_address(self, record):
        address = record["Address"]
        if record["State"].strip():
            address += "\n%s" % record["State"]
        return address

    def unique_slug(self, value, model, slugfield="slug"):
        suffix = 0
        potential = base = slugify(value)
        while True:
            if suffix:
                potential = "-".join([base, str(suffix)])
            if not model.objects.filter(**{slugfield: potential}).count():
                return potential
            # we hit a conflicting slug, so bump the suffix & try again
            suffix += 1
