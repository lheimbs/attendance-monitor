"""Flask config."""
import os

from dotenv import load_dotenv
load_dotenv(verbose=True)


class Config:
    """Flask configuration variables."""

    # General Config
    FLASK_APP = os.environ.get('FLASK_APP')
    FLASK_ENV = os.environ.get('FLASK_ENV')
    SECRET_KEY = os.environ.get('SECRET_KEY')

    DISABLE_CACHE = os.environ.get("FLASK_APP_DISABLE_CACHE", "")
    DISABLE_FORCE_HTTPS = os.environ.get("FLASK_APP_DISABLE_FORCE_HTTPS", "")

    # Static Assets
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

    DEBUG = False
    TESTING = False
    DB_NAME = 'data'
    SECRET_KEY = 'key'
    ADMIN = {
        'username': os.environ.get('FLASK_APP_ADMIN', 'admin'),
        'email': os.environ.get('FLASK_APP_ADMIN_EMAIL', 'admin@admin.de'),
        'password': os.environ.get('FLASK_APP_ADMIN_PASSWORD', 'admin')
    }

    DROP_ALL = os.environ.get('FLASK_APP_DROP_ALL', '')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CSP = {
        # Fonts from fonts.google.com
        'font-src': "'self' themes.googleusercontent.com *.gstatic.com",
        # Used by generated code from http://www.google.com/fonts
        'style-src': [
            "'self'",
            "ajax.googleapis.com fonts.googleapis.com ",
            "*.gstatic.com",
            "'unsafe-inline'",  # sucks but idk how to mitigate this sadly
        ],
        "script-src": [
            "'self'",
            # Due to https://github.com/plotly/dash/issues/630:
            "'sha256-jZlsGVOhUAIcH+4PVs7QuGZkthRMgvT2n0ilH6/zTM0='",
            # "'unsafe-inline'",
        ]
    }

    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(
        os.environ.get('FLASK_APP_DATABASE_USER'),
        os.environ.get('FLASK_APP_DATABASE_PASSWORD'),
        os.environ.get('FLASK_APP_DATABASE_HOST'),
        os.environ.get('FLASK_APP_DATABASE_PORT'),
        os.environ.get('FLASK_APP_DATABASE_NAME')
    )


class ProductionConfig(Config):
    """Uses production database server."""
    DEBUG = False

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True


class DevelopmentConfig(Config):
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///data.db'

    # SQLALCHEMY_BINDS = {
    #     'probe_request': 'sqlite:///data_probes.db',
    #     'users': 'sqlite:///data_users.db',
    # }


config_dict = {
    'production': ProductionConfig,
    'development': DevelopmentConfig,
}
