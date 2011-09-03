"""
Database router class.
"""


class DjqubitRouter(object):
    """A router to control all database operations on models in
    the djqubit application"""

    def db_for_read(self, model, **hints):
        "Point all operations on djqubit models to 'djqubit'"
        if model._meta.app_label == 'djqubit':
            return 'djqubit'
        return None

    def db_for_write(self, model, **hints):
        "Point all operations on djqubit models to 'djqubit'"
        if model._meta.app_label == 'djqubit':
            return 'djqubit'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if a model in djqubit is involved"
        if obj1._meta.app_label == 'djqubit' or obj2._meta.app_label == 'djqubit':
            return True
        return None

    def allow_syncdb(self, db, model):
        "Make sure the djqubit app only appears on the 'djqubit' db"
        if db == 'djqubit':
            return model._meta.app_label == 'djqubit'
        elif model._meta.app_label == 'djqubit':
            return False
        return None


class DjqubitTestRouter(DjqubitRouter):
    """A router to control all database operations on models in
    the djqubit application"""
    def allow_syncdb(self, db, model):
        return True

