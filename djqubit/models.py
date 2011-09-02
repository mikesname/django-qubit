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
    class Meta:
        db_table = "object"
    object_id = models.AutoField(primary_key=True, db_column="id")
    class_name = models.CharField(max_length=255)
    serial_number = models.IntegerField(default=0)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(editable=False)

    def save(self):
        if not self.id:
            self.created_at = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()
        else:
            self.updated_at = datetime.datetime.now()
        super(Object, self).save()

            
class Taxonomy(models.Model, I18NMixin):
    """Taxonomy model."""
    class Meta:
        db_table = "taxonomy"
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    usage = models.CharField(max_length=255, null=True)
    parent = models.ForeignKey("Taxonomy", null=True, related_name="children")
    lft = models.IntegerField()
    rgt = models.IntegerField()
    source_culture = models.CharField(max_length=25)    

    def __repr__(self):
        name = self.get_i18n(FALLBACK_CULTURE, "name")
        if name is not None:
            return "<%s: '%s'>" % (self.__class__.__name__, name)
        return super(Term, self).__repr__()


class TaxonomyI18N(models.Model):
    """Taxonomy Object i18n data."""
    class Meta:
        db_table = "taxonomy_i18n"
    base = models.ForeignKey(Taxonomy, primary_key=True, db_column="id", related_name="i18n")
    name = models.CharField(max_length=255, null=True)
    note = models.TextField(null=True)
    culture = models.CharField(max_length=25)


class Term(Object, I18NMixin):
    """Term model."""
    class Meta:
        db_table = "term"
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    taxonomy = models.ForeignKey(Taxonomy, related_name="terms")
    code = models.CharField(max_length=255)
    parent = models.ForeignKey("Term", related_name="children")
    lft = models.IntegerField()
    rgt = models.IntegerField()
    source_culture = models.CharField(max_length=25)    

    def __repr__(self):
        name = self.get_i18n(FALLBACK_CULTURE, "name")
        if name is not None:
            return "<%s: '%s'>" % (self.__class__.__name__, name)
        return super(Term, self).__repr__()


class TermI18N(models.Model):
    """Term Object i18n data."""
    class Meta:
        db_table = "term_i18n"
    base = models.ForeignKey(Term, primary_key=True, db_column="id", related_name="i18n")
    name = models.CharField(max_length=255, null=True)
    culture = models.CharField(max_length=25)


class Repository(models.Model, I18NMixin):
    """Repository object."""
    class Meta:
        db_table = "repository"
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    identifier = models.CharField(max_length=255, null=True)
    desc_status = models.ForeignKey(Term, null=True, related_name="+")
    desc_detail = models.ForeignKey(Term, null=True, related_name="+")
    desc_identifier = models.CharField(max_length=255, null=True)
    source_culture = models.CharField(max_length=25)    

    def __repr__(self):
        return "<%s: '%s'>" % (self.class_name, self.identifier)


class RepositoryI18N(models.Model):
    """Information Object i18n data."""
    class Meta:
        db_table = "repository_i18n"
    base = models.ForeignKey(Repository, primary_key=True, db_column="id", related_name="i18n")
    geocultural_context = models.TextField(null=True) 
    collecting_policies = models.TextField(null=True) 
    buildings = models.TextField(null=True) 
    holdings = models.TextField(null=True) 
    finding_aids = models.TextField(null=True) 
    opening_times = models.TextField(null=True) 
    access_conditions = models.TextField(null=True) 
    disabled_access = models.TextField(null=True) 
    research_services = models.TextField(null=True) 
    reproduction_services = models.TextField(null=True) 
    public_facilities = models.TextField(null=True) 
    desc_institution_identifier = models.CharField(max_length=255, null=True) 
    desc_rules = models.TextField(null=True) 
    desc_sources = models.TextField(null=True) 
    desc_revision_history = models.TextField(null=True) 
    culture = models.CharField(max_length=25)


class InformationObject(Object, I18NMixin):
    """Information Object model."""
    class Meta:
        db_table = "information_object"
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    identifier = models.CharField(max_length=255, null=True)
    oai_local_identifier = models.IntegerField()
    level_of_description = models.ForeignKey(Term, null=True, related_name="+")
    collection_type = models.ForeignKey(Term, null=True, related_name="+")
    repository = models.ForeignKey(Repository, null=True)
    parent = models.ForeignKey("InformationObject", null=True, related_name="children")
    description_status = models.ForeignKey(Term, null=True, related_name="+")
    description_detail = models.ForeignKey(Term, null=True, related_name="+")
    description_identifier = models.CharField(max_length=255, null=True)
    source_standard = models.CharField(max_length=255, null=True)
    lft = models.IntegerField()
    rgt = models.IntegerField()
    source_culture = models.CharField(max_length=25)    

    def __repr__(self):
        return "<%s: '%s'>" % (self.class_name, self.identifier)


class InformationObjectI18N(models.Model):
    """Information Object i18n data."""
    class Meta:
        db_table = "information_object_i18n"
    base = models.ForeignKey(InformationObject, primary_key=True, db_column="id", related_name="i18n")
    title = models.CharField(max_length=255, null=True)
    alternate_title = models.CharField(max_length=255, null=True)
    edition = models.CharField(max_length=255, null=True)
    extent_and_medium = models.TextField(null=True)
    archival_history = models.TextField(null=True)
    acquisition = models.TextField(null=True)
    scope_and_content = models.TextField(null=True)
    appraisal = models.TextField(null=True)
    accruals = models.TextField(null=True)
    arrangement = models.TextField(null=True)
    access_conditions = models.TextField(null=True)
    reproduction_conditions = models.TextField(null=True)
    physical_characteristics = models.TextField(null=True)
    finding_aids = models.TextField(null=True)
    location_of_originals = models.TextField(null=True)
    location_of_copies = models.TextField(null=True)
    related_units_of_description = models.TextField(null=True)
    institution_responsible_identifier = models.CharField(max_length=255, null=True)
    rules = models.TextField(null=True)
    sources = models.TextField(null=True)
    revision_history = models.TextField(null=True)
    culture = models.CharField(max_length=25)


class Actor(Object, I18NMixin):
    """Actor class."""
    class Meta:
        db_table = "actor"
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    corporate_body_identifiers = models.CharField(max_length=255, null=True)
    entity_type = models.ForeignKey(Term, null=True, related_name="+")
    description_status = models.ForeignKey(Term, null=True, related_name="+")
    description_detail = models.ForeignKey(Term, null=True, related_name="+")
    description_identifier = models.CharField(max_length=255, null=True)
    source_standard = models.CharField(max_length=255, null=True)
    parent = models.ForeignKey("Actor", null=True, related_name="children")
    lft = models.IntegerField()
    rgt = models.IntegerField()
    source_culture = models.CharField(max_length=25)    

    def __repr__(self):
        name = self.get_i18n(FALLBACK_CULTURE, "authorised_form_of_name")
        if name is not None:            
            return "<%s: '%s'>" % (self.class_name, name)
        return super(Actor, self).__repr__()
        

class ActorI18N(models.Model):
    """Actor i18n data."""
    class Meta:
        db_table = "actor_i18n"
    base = models.ForeignKey(Actor, primary_key=True, db_column="id", related_name="i18n")
    authorized_form_of_name = models.CharField(max_length=255, null=True)
    dates_of_existence = models.CharField(max_length=255, null=True)
    history = models.TextField(null=True)
    places = models.TextField(null=True)
    legal_status = models.TextField(null=True)
    functions = models.TextField(null=True)
    mandates = models.TextField(null=True)
    internal_structures = models.TextField(null=True)
    general_context = models.TextField(null=True)
    institution_responsible_identifier = models.CharField(max_length=255, null=True)
    rules = models.TextField(null=True)
    revision_history = models.TextField(null=True)
    culture = models.CharField(max_length=25)


class Event(Object, I18NMixin):
    """Event class."""
    class Meta:
        db_table = "event"
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    start_date = models.DateField(null=True)
    start_time = models.TimeField(null=True)
    end_date = models.DateField(null=True)
    end_time = models.TimeField(null=True)
    type = models.ForeignKey(Term, related_name="+")
    information_object = models.ForeignKey(InformationObject, null=True, related_name="object")
    actor = models.ForeignKey(Actor, null=True, related_name="actor_object")
    source_culture = models.CharField(max_length=25)

    def __repr__(self):
        name = self.get_i18n(FALLBACK_CULTURE, "name")
        if name is not None:
            return "<%s: '%s'>" % (self.class_name, name)
        return super(Event, self).__repr__()


class EventI18N(models.Model):
    """Event i18n data."""
    class Meta:
        db_table = "event_i18n"
    base = models.ForeignKey(Event, primary_key=True, db_column="id", related_name="i18n")
    date = models.CharField(max_length=255, null=True)
    name = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    culture = models.CharField(max_length=25)


class Function(Object, I18NMixin):
    """Function class."""
    class Meta:
        db_table = "function"
    base = models.OneToOneField(Object, primary_key=True, db_column="id")
    type = models.ForeignKey(Term, null=True, related_name="+")
    parent = models.ForeignKey("Function", null=True, related_name="children")
    description_status = models.ForeignKey(Term, null=True, related_name="+")
    description_detail = models.ForeignKey(Term, null=True, related_name="+")
    description_identifier = models.CharField(max_length=255, null=True)
    source_standard = models.CharField(max_length=255, null=True)
    lft = models.IntegerField()
    rgt = models.IntegerField()
    source_culture = models.CharField(max_length=25)    

    def __repr__(self):
        return "<%s: '%s'>" % (self.class_name, self.description_identifier)


class FunctionI18N(models.Model):
    """Function i18n data."""
    class Meta:
        db_table = "function_i18n"
    base = models.ForeignKey(Function, primary_key=True, db_column="id", related_name="i18n")
    authorized_form_of_name = models.CharField(max_length=255, null=True)
    classification = models.CharField(max_length=255, null=True)
    dates = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    history = models.TextField(null=True)
    legislation = models.TextField(null=True)
    institution_identifier = models.TextField(null=True)
    revision_history = models.TextField(null=True)
    rules = models.TextField(null=True)
    sources = models.TextField(null=True)
    culture = models.CharField(max_length=25)



