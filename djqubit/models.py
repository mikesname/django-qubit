from django.db import models
from django.core.exceptions import ObjectDoesNotExist

FALLBACK_CULTURE = "en"


class I18NMixin(object):
    """Mixin for I18N-related methods."""
    def get_i18n(self, culture, name):
        """Get i18n data."""
        try:
            return getattr(self.i18n.get(culture=culture), name)
        except ObjectDoesNotExist:
            return getattr(self.i18n.get(culture=FALLBACK_CULTURE), name)


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
        if not self.id:
            self.created_at = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()
        else:
            self.updated_at = datetime.datetime.now()
        super(Object, self).save()

    def __unicode__(self):
        return "%s: %d" % (self.class_name, self.pk)


class Taxonomy(models.Model, I18NMixin):
    """Taxonomy model."""
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    usage = models.CharField(max_length=255, null=True, blank=True)
    parent = models.ForeignKey("Taxonomy", null=True, blank=True, related_name="children")
    lft = models.IntegerField()
    rgt = models.IntegerField()
    source_culture = models.CharField(max_length=25)

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


class Term(Object, I18NMixin):
    """Term model."""
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    taxonomy = models.ForeignKey(Taxonomy, related_name="terms")
    code = models.CharField(max_length=255, null=True, blank=True)
    parent = models.ForeignKey("Term", null=True, blank=True, related_name="children")
    lft = models.IntegerField()
    rgt = models.IntegerField()
    source_culture = models.CharField(max_length=25)

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


class Actor(Object, I18NMixin):
    """Actor class."""
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    corporate_body_identifiers = models.CharField(max_length=255, null=True, blank=True)
    entity_type = models.ForeignKey(Term, null=True, related_name="entity_type",
            limit_choices_to=dict(
                taxonomy__i18n__culture=FALLBACK_CULTURE,
                taxonomy__i18n__name="Actor Entity Types"))
    description_status = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(
                taxonomy__i18n__culture=FALLBACK_CULTURE,
                taxonomy__i18n__name="Publication Status"))
    description_detail = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(
                taxonomy__i18n__culture=FALLBACK_CULTURE,
                taxonomy__i18n__name="Description Detail Levels"))
    description_identifier = models.CharField(max_length=255, null=True, blank=True)
    source_standard = models.CharField(max_length=255, null=True, blank=True)
    parent = models.ForeignKey("Actor", null=True, blank=True, related_name="children")
    lft = models.IntegerField()
    rgt = models.IntegerField()
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


class Repository(Actor, I18NMixin):
    """Repository object."""
    base_actor = models.OneToOneField(Actor, primary_key=True, db_column="id")
    identifier = models.CharField(max_length=255, null=True, blank=True)
    desc_status = models.ForeignKey(Term, null=True, blank=True, db_column="desc_status_id", related_name="+",
            limit_choices_to=dict(
                taxonomy__i18n__culture=FALLBACK_CULTURE,
                taxonomy__i18n__name="Publication Status"))
    desc_detail = models.ForeignKey(Term, null=True, blank=True, db_column="desc_detail_id", related_name="+",
            limit_choices_to=dict(
                taxonomy__i18n__culture=FALLBACK_CULTURE,
                taxonomy__i18n__name="Description Detail Levels"))
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


class InformationObject(Object, I18NMixin):
    """Information Object model."""
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    identifier = models.CharField(max_length=255, null=True, blank=True)
    oai_local_identifier = models.IntegerField()
    level_of_description = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(
                taxonomy__i18n__culture=FALLBACK_CULTURE,
                taxonomy__i18n__name="Levels of description"))
    collection_type = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(
                taxonomy__i18n__culture=FALLBACK_CULTURE,
                taxonomy__i18n__name="Collection Types"))
    repository = models.ForeignKey(Repository, null=True, blank=True, related_name="information_objects")
    parent = models.ForeignKey("InformationObject", null=True, blank=True, related_name="children")
    description_status = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(
                taxonomy__i18n__culture=FALLBACK_CULTURE,
                taxonomy__i18n__name="Publication Status"))
    description_detail = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(
                taxonomy__i18n__culture=FALLBACK_CULTURE,
                taxonomy__i18n__name="Description Detail Levels"))
    description_identifier = models.CharField(max_length=255, null=True, blank=True)
    source_standard = models.CharField(max_length=255, null=True, blank=True)
    lft = models.IntegerField()
    rgt = models.IntegerField()
    source_culture = models.CharField(max_length=25)

    class Meta:
        db_table = "information_object"

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
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    start_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    type = models.ForeignKey(Term, related_name="type")
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


class Function(Object, I18NMixin):
    """Function class."""
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    type = models.ForeignKey(Term, null=True, related_name="+")
    parent = models.ForeignKey("Function", null=True, blank=True, related_name="children")
    description_status = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(
                taxonomy__i18n__culture=FALLBACK_CULTURE,
                taxonomy__i18n__name="Publication Status"))
    description_detail = models.ForeignKey(Term, null=True, blank=True, related_name="+",
            limit_choices_to=dict(
                taxonomy__i18n__culture=FALLBACK_CULTURE,
                taxonomy__i18n__name="Description Detail Levels"))
    description_identifier = models.CharField(max_length=255, null=True, blank=True)
    source_standard = models.CharField(max_length=255, null=True, blank=True)
    lft = models.IntegerField(null=True, blank=True)
    rgt = models.IntegerField(null=True, blank=True)
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


class Property(models.Model, I18NMixin):
    """Property class."""
    base = models.ForeignKey(Object, related_name="properties", db_column="object_id")
    scope = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(editable=False)
    source_culture = models.CharField(max_length=25)
    serial_number = models.IntegerField(default=0)

    class Meta:
        db_table = "property"

    def save(self):
        if not self.id:
            self.created_at = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()
        else:
            self.updated_at = datetime.datetime.now()
        super(Object, self).save()


class PropertyI18N(models.Model):
    """Propery I18N data."""
    base = models.ForeignKey(Property, primary_key=True, db_column="id", related_name="i18n")
    value = models.CharField(max_length=255, null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "property_i18n"


class OtherName(models.Model, I18NMixin):
    """Other Name class"""
    base = models.ForeignKey(Object, related_name="other_names", db_column="object_id")
    type = models.ForeignKey(Term, null=True, related_name="+")
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(editable=False)
    source_culture = models.CharField(max_length=25)
    serial_number = models.IntegerField(default=0)

    class Meta:
        db_table = "other_name"

    def save(self):
        if not self.id:
            self.created_at = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()
        else:
            self.updated_at = datetime.datetime.now()
        super(Object, self).save()


class OtherNameI18N(models.Model):
    """Other Name I18N data."""
    base = models.ForeignKey(OtherName, primary_key=True, db_column="id", related_name="i18n")
    name = models.CharField(max_length=255, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    culture = models.CharField(max_length=25)

    class Meta:
        db_table = "other_name_i18n"

