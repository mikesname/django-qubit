"""
DjQubit Models.
"""

import datetime

from django.db import models, connections, transaction, router
from django.db.models import F, Max
from django.core.exceptions import ObjectDoesNotExist, ValidationError

FALLBACK_CULTURE = "en"


class I18NValidationError(ValidationError):
    pass


def dict_cursor(cursor):
    description = [x[0] for x in cursor.description]
    for row in cursor:
        yield dict(zip(description, row))


class I18NMixin(object):
    """Mixin for I18N-related methods."""
    def get_i18n(self, culture, name):
        """Get i18n data."""
        try:                                                 
            return getattr(self.i18n.get(culture=culture), name)
        except ObjectDoesNotExist:
            return getattr(self.i18n.get(culture=FALLBACK_CULTURE), name)        

    def set_i18n(self, culture, data):
        """Set i18n data for a model."""
        if not self.pk:
            raise I18NValidationError("Cannot set i18n data on an unsaved model")

        fields = self.i18n.model._meta.get_all_field_names()

        # FIXME: This is VERY fragile in it's current state
        table = self._meta.db_table
        cursor = connections[router.db_for_read(self.__class__)].cursor()
        findquery = "SELECT * FROM %s_i18n WHERE id=%%s AND culture=%%s" % self._meta.db_table
        cursor.execute(findquery, [self.pk, culture])
        row = cursor.fetchone()
        args = [kv for kv in data.iteritems() if kv[0] in fields]
        uquery = None
        if row is not None:
            fstr = ", ".join(["%s=%%s" % k[0] for k in args])
            uquery = "UPDATE %s_i18n SET %s WHERE id=%%s AND culture=%%s" % (table, fstr)
        else:
            kstr = ", ".join([a[0] for a in args]) 
            vstr = ", ".join(['%s' for a in args])
            uquery = "INSERT INTO %s_i18n (%s,id,culture) VALUES (%s,%%s,%%s)" % (
                    table, kstr, vstr)
        cursor.execute(uquery, [a[1] for a in args] + [self.pk, culture])
        transaction.commit_unless_managed(using=router.db_for_write(self.__class__))


class Object(models.Model):
    """Object model."""
    object_id = models.AutoField(primary_key=True, db_column="id")
    class_name = models.CharField(max_length=255)
    serial_number = models.IntegerField(default=0)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(editable=False)

    class Meta:
        db_table = "object"

    def save(self):
        if not self.object_id:
            self.created_at = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()
        else:
            self.updated_at = datetime.datetime.now()
        if not self.class_name:
            self.class_name = "Qubit%s" % self.__class__.__name__
        super(Object, self).save()

    def __unicode__(self):
        return "%s: %d" % (self.class_name, self.pk)


class NestedObject(Object):
    """
    Base class for classes with lft/rgt heirarchy fields.  These creates a
    tree structure which allows for optimised traversal, as opposed to
    crawling the heirarchy via the database.
    """
    id = models.OneToOneField(Object, primary_key=True, db_column="id")
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children")
    lft = models.PositiveIntegerField()
    rgt = models.PositiveIntegerField()

    class Meta:
        abstract = True
        ordering = ["-lft"]

    def update_nested_set(self):
        """Update nested tree values for this model."""
        delta = 2
        shift = 0
        if self.lft and self.rgt:
            delta = self.rgt - self.lft + 1
        cls = self.__class__
        if self.parent is None:
            maxrgt = cls.objects.aggregate(Max("rgt"))["rgt__max"]
            if not self.lft or not self.rgt:
                self.lft = maxrgt + 1
                self.rgt = maxrgt + 2
                return
            shift = maxrgt + 1 - self.lft
        else:
            cls.objects.filter(lft__gte=self.parent.rgt).update(lft=F('lft') + delta)
            cls.objects.filter(rgt__gte=self.parent.rgt).update(rgt=F('rgt') + delta)
            if not self.lft or not self.rgt:
                self.lft = self.parent.rgt
                self.rgt = self.parent.rgt + 1
                self.parent.rgt += 2
                return
            if self.lft > self.parent.rgt:
                self.lft += delta
                self.rgt += delta
                shift = self.parent.rgt - self.lft
        cls.objects.filter(lft__gte=self.lft, rgt__lte=self.rgt)\
                .update(lft=F('lft') + shift, rgt=F('rgt') + shift)
        self.delete_nested_set()
        if shift > 0:
            self.lft -= delta
            self.rgt -= delta
        self.lft += shift
        self.rgt += shift

    def delete_nested_set(self):
        """Delete nested tree values for this model."""
        delta = self.rgt - self.lft + 1
        cls = self.__class__
        cls.objects.filter(lft__gte=self.rgt).update(lft=F('lft') - delta)
        cls.objects.filter(rgt__gte=self.rgt).update(rgt=F('rgt') - delta)
        return

    def save(self, *args, **kwargs):
        """Update tree-structure on when created or when parent has changed."""
        if self.pk is None:
           self.update_nested_set()
        else:
            dbself = self.__class__.objects.get(pk=self.pk)
            if dbself.parent != self.parent:
                self.update_nested_set()
        super(NestedObject, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Update tree structure on save."""
        self.delete_nested_set()
        super(NestedObject, self).delete(*args, **kwargs)


class Taxonomy(NestedObject, I18NMixin):
    """Taxonomy model."""
    usage = models.CharField(max_length=255, null=True, blank=True)
    source_culture = models.CharField(max_length=25)

    # Qubit primary keys are hard-coded for these items
    ROOT_ID = 30
    DESCRIPTION_DETAIL_LEVEL_ID = 31
    ACTOR_ENTITY_TYPE_ID = 32
    DESCRIPTION_STATUS_ID = 33
    LEVEL_OF_DESCRIPTION_ID = 34
    SUBJECT_ID = 35
    ACTOR_NAME_TYPE_ID = 36
    NOTE_TYPE_ID = 37
    REPOSITORY_TYPE_ID = 38
    EVENT_TYPE_ID = 40
    QUBIT_SETTING_LABEL_ID = 41
    PLACE_ID = 42
    FUNCTION_ID = 43
    HISTORICAL_EVENT_ID = 44
    COLLECTION_TYPE_ID = 45
    MEDIA_TYPE_ID = 46
    DIGITAL_OBJECT_USAGE_ID = 47
    PHYSICAL_OBJECT_TYPE_ID = 48
    RELATION_TYPE_ID = 49
    MATERIAL_TYPE_ID = 50
    RAD_NOTE_ID = 51
    RAD_TITLE_NOTE_ID = 52
    MODS_RESOURCE_TYPE_ID = 53
    DC_TYPE_ID = 54
    ACTOR_RELATION_TYPE_ID = 55
    RELATION_NOTE_TYPE_ID = 56
    TERM_RELATION_TYPE_ID = 57
    STATUS_TYPE_ID = 59
    PUBLICATION_STATUS_ID = 60
    ISDF_RELATION_TYPE_ID = 61

    class Meta:
        db_table = "taxonomy"

    def __repr__(self):
        name = self.get_i18n(FALLBACK_CULTURE, "name")
        if name is not None:
            return "<%s: '%s'>" % (self.__class__.__name__, name)
        return super(Term, self).__repr__()

    def __unicode__(self):
        name = self.get_i18n(FALLBACK_CULTURE, "name")
        if name is None:
            return "Taxonomy: %d" % self.pk
        return name


class TaxonomyI18N(models.Model):
    """Taxonomy Object i18n data."""
    base = models.ForeignKey(Taxonomy, primary_key=True, db_column="id", related_name="i18n")
    name = models.CharField(max_length=255, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "taxonomy_i18n"


class Term(NestedObject, I18NMixin):
    """Term model."""
    taxonomy = models.ForeignKey(Taxonomy, related_name="terms")
    code = models.CharField(max_length=255, null=True, blank=True)
    source_culture = models.CharField(max_length=25)

    # ROOT term id
    ROOT_ID = 110

    # Event type taxonomy
    CREATION_ID = 111
    CUSTODY_ID = 113
    PUBLICATION_ID = 114
    CONTRIBUTION_ID = 115
    COLLECTION_ID = 117
    ACCUMULATION_ID = 118

    # Note type taxonomy
    TITLE_NOTE_ID = 119
    PUBLICATION_NOTE_ID = 120
    SOURCE_NOTE_ID = 121
    SCOPE_NOTE_ID = 122
    DISPLAY_NOTE_ID = 123
    ARCHIVIST_NOTE_ID = 124
    GENERAL_NOTE_ID = 125
    OTHER_DESCRIPTIVE_DATA_ID = 126
    MAINTENANCE_NOTE_ID = 127

    # Collection type taxonomy
    ARCHIVAL_MATERIAL_ID = 128
    PUBLISHED_MATERIAL_ID = 129
    ARTEFACT_MATERIAL_ID = 130

    # Actor type taxonomy
    CORPORATE_BODY_ID = 131
    PERSON_ID = 132
    FAMILY_ID = 133

    # Other name type taxonomy
    FAMILY_NAME_FIRST_NAME_ID = 134

    # Media type taxonomy
    AUDIO_ID = 135
    IMAGE_ID = 136
    TEXT_ID = 137
    VIDEO_ID = 138
    OTHER_ID = 139

    # Digital object usage taxonomy
    MASTER_ID = 140
    REFERENCE_ID = 141
    THUMBNAIL_ID = 142
    COMPOUND_ID = 143

    # Physical object type taxonomy
    LOCATION_ID = 144
    CONTAINER_ID = 145
    ARTEFACT_ID = 146

    # Relation type taxonomy
    HAS_PHYSICAL_OBJECT_ID = 147

    # Actor name type taxonomy
    PARALLEL_FORM_OF_NAME_ID = 148
    OTHER_FORM_OF_NAME_ID = 149

    # Actor relation type taxonomy
    HIERARCHICAL_RELATION_ID = 150
    TEMPORAL_RELATION_ID = 151
    FAMILY_RELATION_ID = 152
    ASSOCIATIVE_RELATION_ID = 153

    # Actor relation note taxonomy
    RELATION_NOTE_DESCRIPTION_ID = 154
    RELATION_NOTE_DATE_ID = 155

    # Term relation taxonomy
    ALTERNATIVE_LABEL_ID = 156
    TERM_RELATION_ASSOCIATIVE_ID = 157

    # Status type taxonomy
    STATUS_TYPE_PUBLICATION_ID = 158

    # Publication status taxonomy
    PUBLICATION_STATUS_DRAFT_ID = 159
    PUBLICATION_STATUS_PUBLISHED_ID = 160

    # Name access point
    NAME_ACCESS_POINT_ID = 161

    # Function relation type taxonomy
    ISDF_HIERARCHICAL_RELATION_ID = 162
    ISDF_TEMPORAL_RELATION_ID = 163
    ISDF_ASSOCIATIVE_RELATION_ID = 164

    # ISAAR standardized form name
    STANDARDIZED_FORM_OF_NAME_ID = 165

    # External URI
    EXTERNAL_URI_ID = 166

    class Meta:
        db_table = "term"

    def __repr__(self):
        name = self.get_i18n(FALLBACK_CULTURE, "name")
        if name is not None:
            return "<%s: '%s'>" % (self.__class__.__name__, name)
        return super(Term, self).__repr__()

    def __unicode__(self):
        name = self.get_i18n(FALLBACK_CULTURE, "name")
        if name is None:
            name = "<Null>"
        return name


class TermI18N(models.Model):
    """Term Object i18n data."""
    base = models.ForeignKey(Term, primary_key=True, db_column="id", related_name="i18n")
    name = models.CharField(max_length=255, null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "term_i18n"

    def __repr__(self):
        return "<%s: '%s'>" % (self.__class__.__name__, self.culture)


class Relation(Object):
    """Relationship object."""
    id = models.OneToOneField(Object, primary_key=True, db_column="id")
    subject = models.ForeignKey(Object, db_column="subject_id", related_name="relations")
    object = models.ForeignKey(Object, db_column="object_id", related_name="objects")
    type = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.RELATION_TYPE_ID))
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "relation"


class Actor(NestedObject, I18NMixin):
    """Actor class."""
    corporate_body_identifiers = models.CharField(max_length=255, null=True, blank=True)
    entity_type = models.ForeignKey(Term, null=True, blank=True, related_name="entity_type",
            limit_choices_to=dict(taxonomy=Taxonomy.ACTOR_ENTITY_TYPE_ID))
    description_status = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.DESCRIPTION_STATUS_ID))
    description_detail = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.DESCRIPTION_DETAIL_LEVEL_ID))
    description_identifier = models.CharField(max_length=255, null=True, blank=True)
    source_standard = models.CharField(max_length=255, null=True, blank=True)
    source_culture = models.CharField(max_length=25)

    class Meta:
        db_table = "actor"

    def __repr__(self):
        name = self.get_i18n(FALLBACK_CULTURE, "authorized_form_of_name")
        if name is not None:
            return "<%s: '%s'>" % (self.class_name, name)
        return super(Actor, self).__repr__()

    def __unicode__(self):
        name = self.get_i18n(FALLBACK_CULTURE, "authorized_form_of_name")
        if name is None:
            return "Actor: %d" % self.pk
        return name


class ActorI18N(models.Model):
    """Actor i18n data."""
    base = models.ForeignKey(Actor, primary_key=True, db_column="id", related_name="i18n")
    authorized_form_of_name = models.CharField(max_length=255, null=True, blank=True)
    dates_of_existence = models.CharField(max_length=255, null=True, blank=True)
    history = models.TextField(null=True, blank=True)
    places = models.TextField(null=True, blank=True)
    legal_status = models.TextField(null=True, blank=True)
    functions = models.TextField(null=True, blank=True)
    mandates = models.TextField(null=True, blank=True)
    internal_structures = models.TextField(null=True, blank=True)
    general_context = models.TextField(null=True, blank=True)
    institution_responsible_identifier = models.CharField(max_length=255, null=True, blank=True)
    rules = models.TextField(null=True, blank=True)
    revision_history = models.TextField(null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "actor_i18n"


class Repository(Actor):
    """Repository object."""
    base_actor = models.OneToOneField(Actor, primary_key=True, db_column="id")
    identifier = models.CharField(max_length=255, null=True, blank=True)
    desc_status = models.ForeignKey(Term, null=True, blank=True,
            db_column="desc_status_id", related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.DESCRIPTION_STATUS_ID))
    desc_detail = models.ForeignKey(Term, null=True, blank=True,
            db_column="desc_detail_id", related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.DESCRIPTION_DETAIL_LEVEL_ID))
    repository_description_identifier = models.CharField(max_length=255, db_column="desc_identifier", null=True, blank=True)
    repository_source_culture = models.CharField(max_length=25, db_column="source_culture")

    class Meta:
        db_table = "repository"

    def __repr__(self):
        return "<%s: '%s'>" % (self.class_name, self.identifier)

    def __unicode__(self):
        name = self.identifier
        if name is None:
            name = "Repository: %d" % self.pk
        return name


class RepositoryI18N(models.Model):
    """Information Object i18n data."""
    base = models.ForeignKey(Repository, primary_key=True, db_column="id", related_name="repository_i18n")
    geocultural_context = models.TextField(null=True, blank=True)
    collecting_policies = models.TextField(null=True, blank=True)
    buildings = models.TextField(null=True, blank=True)
    holdings = models.TextField(null=True, blank=True)
    finding_aids = models.TextField(null=True, blank=True)
    opening_times = models.TextField(null=True, blank=True)
    access_conditions = models.TextField(null=True, blank=True)
    disabled_access = models.TextField(null=True, blank=True)
    research_services = models.TextField(null=True, blank=True)
    reproduction_services = models.TextField(null=True, blank=True)
    public_facilities = models.TextField(null=True, blank=True)
    desc_institution_identifier = models.CharField(max_length=255, null=True, blank=True)
    desc_rules = models.TextField(null=True, blank=True)
    desc_sources = models.TextField(null=True, blank=True)
    desc_revision_history = models.TextField(null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "repository_i18n"


class User(Actor):
    """Qubit User class.  Unfortunately we can't seem
    to reuse the Django auth user class here.
    NB: Deliberately left blank=True off the fields"""
    base_actor = models.OneToOneField(Actor, primary_key=True, db_column="id")
    username = models.CharField(max_length=255, unique=True, null=True)
    email = models.CharField(max_length=255, null=True)
    sha1_password = models.CharField(max_length=255, null=True)
    salt = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = "user"


class InformationObject(NestedObject, I18NMixin):
    """Information Object model."""
    identifier = models.CharField(max_length=255, null=True, blank=True)
    oai_local_identifier = models.PositiveIntegerField(unique=True)
    level_of_description = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.LEVEL_OF_DESCRIPTION_ID))
    collection_type = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.COLLECTION_TYPE_ID))
    repository = models.ForeignKey(Repository, null=True, blank=True, related_name="information_objects")
    description_status = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.DESCRIPTION_STATUS_ID))
    description_detail = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.DESCRIPTION_DETAIL_LEVEL_ID))
    description_identifier = models.CharField(max_length=255, null=True, blank=True)
    source_standard = models.CharField(max_length=255, null=True, blank=True)
    source_culture = models.CharField(max_length=25)

    class Meta:
        db_table = "information_object"

    def save(self, *args, **kwargs):
        """Update oai_local_identifier on save."""
        if self.oai_local_identifier is None:
            self.oai_local_identifier = self._new_oai_local_identifier()
        super(InformationObject, self).save(*args, **kwargs)

    def _new_oai_local_identifier(self):
        return self.__class__.objects\
                .aggregate(Max("oai_local_identifier"))\
                ["oai_local_identifier__max"] + 1

    def __repr__(self):
        return "<%s: '%s'>" % (self.class_name, self.identifier)

    def __unicode__(self):
        name = self.identifier
        if name is None:
            name = "Information object: %d" % self.pk
        return name


class InformationObjectI18N(models.Model):
    """Information Object i18n data."""
    base = models.ForeignKey(InformationObject, primary_key=True, db_column="id", related_name="i18n")
    title = models.CharField(max_length=255, null=True, blank=True)
    alternate_title = models.CharField(max_length=255, null=True, blank=True)
    edition = models.CharField(max_length=255, null=True, blank=True)
    extent_and_medium = models.TextField(null=True, blank=True)
    archival_history = models.TextField(null=True, blank=True)
    acquisition = models.TextField(null=True, blank=True)
    scope_and_content = models.TextField(null=True, blank=True)
    appraisal = models.TextField(null=True, blank=True)
    accruals = models.TextField(null=True, blank=True)
    arrangement = models.TextField(null=True, blank=True)
    access_conditions = models.TextField(null=True, blank=True)
    reproduction_conditions = models.TextField(null=True, blank=True)
    physical_characteristics = models.TextField(null=True, blank=True)
    finding_aids = models.TextField(null=True, blank=True)
    location_of_originals = models.TextField(null=True, blank=True)
    location_of_copies = models.TextField(null=True, blank=True)
    related_units_of_description = models.TextField(null=True, blank=True)
    institution_responsible_identifier = models.CharField(max_length=255, null=True, blank=True)
    rules = models.TextField(null=True, blank=True)
    sources = models.TextField(null=True, blank=True)
    revision_history = models.TextField(null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "information_object_i18n"


class Event(Object, I18NMixin):
    """Event class."""
    id = models.OneToOneField(Object, primary_key=True, db_column="id")
    start_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    type = models.ForeignKey(Term, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.EVENT_TYPE_ID))
    information_object = models.ForeignKey(InformationObject, null=True, related_name="events")
    actor = models.ForeignKey(Actor, null=True, related_name="actor_object")
    source_culture = models.CharField(max_length=25)

    class Meta:
        db_table = "event"

    def __repr__(self):
        name = self.get_i18n(FALLBACK_CULTURE, "name")
        if name is not None:
            return "<%s: '%s'>" % (self.class_name, name)
        return super(Event, self).__repr__()

    def __unicode__(self):
        name = self.get_i18n(FALLBACK_CULTURE, "name")
        if name is None:
            return "Event: %d" % self.pk
        return name


class EventI18N(models.Model):
    """Event i18n data."""
    base = models.ForeignKey(Event, primary_key=True, db_column="id", related_name="i18n")
    date = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "event_i18n"


class Function(NestedObject, I18NMixin):
    """Function class."""
    type = models.ForeignKey(Term, null=True, related_name="+")
    description_status = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.DESCRIPTION_STATUS_ID))
    description_detail = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.DESCRIPTION_DETAIL_LEVEL_ID))
    description_identifier = models.CharField(max_length=255, null=True, blank=True)
    source_standard = models.CharField(max_length=255, null=True, blank=True)
    source_culture = models.CharField(max_length=25)

    class Meta:
        db_table = "function"

    def __repr__(self):
        return "<%s: '%s'>" % (self.class_name, self.description_identifier)


class FunctionI18N(models.Model):
    """Function i18n data."""
    base = models.ForeignKey(Function, primary_key=True, db_column="id", related_name="i18n")
    authorized_form_of_name = models.CharField(max_length=255, null=True, blank=True)
    classification = models.CharField(max_length=255, null=True, blank=True)
    dates = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    history = models.TextField(null=True, blank=True)
    legislation = models.TextField(null=True, blank=True)
    institution_identifier = models.TextField(null=True, blank=True)
    revision_history = models.TextField(null=True, blank=True)
    rules = models.TextField(null=True, blank=True)
    sources = models.TextField(null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "function_i18n"


class DigitalObject(NestedObject):
    """Digital object class."""
    # NB: The schema changes between Qubit 1.1 and 1.2 with regard to
    # checksum_type.
    information_object = models.ForeignKey(InformationObject, null=True, blank=True,
            related_name="digital_objects")
    usage = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.DIGITAL_OBJECT_USAGE_ID))
    mime_type = models.CharField(max_length=255, null=True, blank=True)
    media_type = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.MEDIA_TYPE_ID))
    name = models.CharField(max_length=255, null=True, blank=True)
    path = models.CharField(max_length=255, null=True, blank=True)
    sequence = models.PositiveIntegerField(null=True, blank=True)
    byte_size = models.PositiveIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=255, null=True, blank=True)
    checksum_type = models.ForeignKey(Term, null=True, blank=True, related_name="+")

    class Meta:
        db_table = "digital_object"


class Property(models.Model, I18NMixin):
    """Property class."""
    object_id = models.ForeignKey(Object, related_name="properties", db_column="object_id")
    scope = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(editable=False)
    source_culture = models.CharField(max_length=25)
    serial_number = models.IntegerField(default=0)

    class Meta:
        db_table = "property"

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()
        else:
            self.updated_at = datetime.datetime.now()
        super(Property, self).save(*args, **kwargs)


class PropertyI18N(models.Model):
    """Propery I18N data."""
    base = models.ForeignKey(Property, primary_key=True, db_column="id", related_name="i18n")
    value = models.CharField(max_length=255, null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "property_i18n"


class OtherName(models.Model, I18NMixin):
    """Other Name class"""
    object_id = models.ForeignKey(Object, related_name="other_names", db_column="object_id")
    type = models.ForeignKey(Term, null=True, related_name="+")
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(editable=False)
    source_culture = models.CharField(max_length=25)
    serial_number = models.IntegerField(default=0)

    class Meta:
        db_table = "other_name"

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()
        else:
            self.updated_at = datetime.datetime.now()
        super(OtherName, self).save(*args, **kwargs)


class OtherNameI18N(models.Model):
    """Other Name I18N data."""
    base = models.ForeignKey(OtherName, primary_key=True, db_column="id", related_name="i18n")
    name = models.CharField(max_length=255, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "other_name_i18n"


class ContactInformation(models.Model, I18NMixin):
    """Contact object."""
    actor = models.ForeignKey(Actor, related_name="contacts")
    primary_contact = models.NullBooleanField(null=True)
    contact_person = models.CharField(max_length=255, null=True, blank=True)
    street_address = models.TextField(null=True, blank=True)
    website = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    telephone = models.CharField(max_length=255, null=True, blank=True)
    fax = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=255, null=True, blank=True)
    country_code = models.CharField(max_length=255, null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(editable=False)
    source_culture = models.CharField(max_length=25)
    serial_number = models.IntegerField(default=0)

    class Meta:
        db_table = "contact_information"

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()
        else:
            self.updated_at = datetime.datetime.now()
        super(ContactInformation, self).save(*args, **kwargs)


class ContactInformationI18N(models.Model):
    """Contact I18N data."""
    base = models.ForeignKey(ContactInformation, primary_key=True, db_column="id", related_name="i18n")
    contact_type = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    region = models.CharField(max_length=255, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "contact_information_i18n"


class Note(models.Model, I18NMixin):
    """Note class"""
    # FIXME: in Qubit 1.1 QubitNote has nested set behaviour, which was
    # removed in Qubit 1.2-dev.  We're going to ignore this for now
    # which avoids making the Note class a NestedObject.  We do need
    # the columns for compatibility though.
    object_id = models.ForeignKey(Object, related_name="notes", db_column="object_id")
    type = models.ForeignKey(Term, null=True, related_name="+",
            limit_choices_to=dict(taxonomy=Taxonomy.NOTE_TYPE_ID))
    scope = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, null=True)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children")
    lft = models.PositiveIntegerField(default=0)
    rgt = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(editable=False)
    source_culture = models.CharField(max_length=25)
    serial_number = models.IntegerField(default=0)

    class Meta:
        db_table = "note"

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()
        else:
            self.updated_at = datetime.datetime.now()
        super(Note, self).save(*args, **kwargs)


    def __unicode__(self):
        return "Note: %s" % str(self.created_at)


class NoteI18N(models.Model):
    """Note I18N data."""
    base = models.ForeignKey(Note, primary_key=True, db_column="id", related_name="i18n")
    content = models.TextField(null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "note_i18n"


class Slug(models.Model):
    """Slug class."""
    object_id = models.OneToOneField(Object, related_name="slug", db_column="object_id")
    slug = models.CharField(max_length=255, unique=True)
    serial_number = models.IntegerField(default=0)

    class Meta:
        db_table = "slug"

    def __unicode__(self):
        return self.slug


