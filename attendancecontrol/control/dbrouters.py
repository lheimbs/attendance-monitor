from .models.probes import ProbeRequests

class ProbeRequestsRouter(object):

    def db_for_read(self, model, **hints):
        """ reading ProbeRequests from probes DB """
        if model == ProbeRequests:
            return 'probes'
        return None

    def db_for_write(self, model, **hints):
        """ writing SomeModel to otherdb """
        if model == ProbeRequests:
            raise Exception("Probes can only be read from this app!")
        return None
