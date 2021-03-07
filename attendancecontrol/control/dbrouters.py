from .models.probes import ProbeRequests

class ProbeRequestsRouter(object):      # pragma: no cover

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the auth and contenttypes apps only appear in the
        'auth_db' database.
        """
        if db == "probes":
            if model_name == ProbeRequests._meta.model_name:
                return True
            else:
                return False
        elif model_name == ProbeRequests._meta.model_name:
            return False
            # return db == 'auth_db'
        return None

    def db_for_read(self, model, **hints):
        """ reading ProbeRequests from probes DB """
        if model == ProbeRequests:
            return 'probes'
        return 'default'

    def db_for_write(self, model, **hints):
        """ writing SomeModel to otherdb """
        if model == ProbeRequests:
            raise Exception("Probes can only be read from this app!")
        return None
