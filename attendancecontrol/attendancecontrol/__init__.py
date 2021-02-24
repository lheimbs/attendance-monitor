"""Initialize Flask app."""
from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_bootstrap import Bootstrap
from flask_nav import Nav

from .config import init_config
from .base import base_bp
from .home import home_bp
from .student import student_bp
from .teacher import teacher_bp
from .auth import auth_bp, init_login
from .models import db, init_db
from .assets import compile_assets

csrf = CSRFProtect()
talisman = Talisman()
nav = Nav()


def register_blueprints(app):
    app.register_blueprint(base_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)


def create_app():
    """Construct core Flask application with embedded Dash app."""
    app = Flask(__name__, instance_relative_config=False)

    init_config(app)
    csrf.init_app(app)
    init_db(app)
    init_login(app)

    Bootstrap(app)
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True  # TODO: serve localy in prod?

    # nav.init_app(app)

    # from .errors import register_handlers
    # register_handlers(app)

    with app.app_context(), app.test_request_context():
        # from .models import db          # noqa: F841
        Migrate(app, db)

        disable_https = app.config['DISABLE_FORCE_HTTPS']
        if disable_https:
            app.logger.debug("Disabling talismans https forcing!")
        talisman.init_app(
            app,
            force_https=bool(disable_https),
            content_security_policy=app.config['CSP'],
            content_security_policy_nonce_in=['script-src'],
        )
        register_blueprints(app)

        # Compile assets
        compile_assets(app)

    return app
