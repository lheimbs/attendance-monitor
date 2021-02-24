from flask_login import AnonymousUserMixin

class MyAnonymousUser(AnonymousUserMixin):
    is_admin = False
