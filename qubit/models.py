from django.db import models


class Object(models.Model):
    """Object model."""
    class Meta:
        db_table = "object"

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


class Term(models.Model):
    """Term model."""
    class Meta:
        db_table = "term"
    id = models.OneToOneField(Object, primary_key=True, db_column="id")
    code = models.CharField(max_length=255)
    parent = models.ForeignKey("Term", related_name="children")
    lft = models.IntegerField()
    rgt = models.IntegerField()
    source_culture = models.CharField(max_length=25)    

class TermI18N(models.Model):
    """Term Object i18n data."""
    class Meta:
        db_table = "term_i18n"
    id = models.ForeignKey(Term, primary_key=True, db_column="id")
    name = models.CharField(max_length=255, null=True)
    culture = models.CharField(max_length=25)


class Taxonomy(models.Model):
    """Taxonomy model."""
    class Meta:
        db_table = "taxonomy"
    id = models.OneToOneField(Object, primary_key=True, db_column="id")
    usage = models.CharField(max_length=255, null=True)
    parent = models.ForeignKey("Taxonomy", null=True, related_name="children")
    lft = models.IntegerField()
    rgt = models.IntegerField()
    source_culture = models.CharField(max_length=25)    

class TaxonomyI18N(models.Model):
    """Taxonomy Object i18n data."""
    class Meta:
        db_table = "taxonomy_i18n"
    id = models.ForeignKey(Taxonomy, primary_key=True, db_column="id")
    name = models.CharField(max_length=255, null=True)
    note = models.TextField(null=True)
    culture = models.CharField(max_length=25)




class Repository(models.Model):
    """Repository object."""
    class Meta:
        db_table = "repository"
    id = models.OneToOneField(Object, primary_key=True, db_column="id")
    identifier = models.CharField(max_length=255, null=True)
    desc_status = models.ForeignKey(Term, null=True, related_name="+")
    desc_detail = models.ForeignKey(Term, null=True, related_name="+")
    desc_identifier = models.CharField(max_length=255, null=True)
    source_culture = models.CharField(max_length=25)    

class RepositoryI18N(models.Model):
    """Information Object i18n data."""
    class Meta:
        db_table = "repository_i18n"
    id = models.ForeignKey(Repository, primary_key=True, db_column="id")
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



class InformationObject(models.Model):
    """Information Object model."""
    class Meta:
        db_table = "information_object"

    id = models.OneToOneField(Object, primary_key=True, db_column="id")
    identifier = models.CharField(max_length=255, null=True)
    oai_local_identifier = models.IntegerField()
    level_of_description = models.ForeignKey(Term, null=True)
    collection_type = models.ForeignKey(Term, null=True, related_name="+")
    repository = models.ForeignKey(Repository, null=True)
    parent = models.ForeignKey("InformationObject", null=True)
    description_status = models.ForeignKey(Term, null=True, related_name="+")
    description_detail = models.ForeignKey(Term, null=True, related_name="+")
    description_identifier = models.CharField(max_length=255, null=True)
    source_standard = models.CharField(max_length=255, null=True)
    lft = models.IntegerField()
    rgt = models.IntegerField()
    source_culture = models.CharField(max_length=25)    

class InformationObjectI18N(models.Model):
    """Information Object i18n data."""
    class Meta:
        db_table = "information_object_i18n"
    id = models.ForeignKey(InformationObject, primary_key=True, db_column="id")
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


