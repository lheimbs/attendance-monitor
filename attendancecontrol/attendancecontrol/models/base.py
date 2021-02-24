from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from sqlalchemy import exc as sqlalchemy_exc, func as sqlalchemy_func
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class BaseMixin(object):
    def save_to_db(self):
        db.session.add(self)
        self.db_commit()

    def delete_from_db(self):
        db.session.delete(self)
        self.db_commit()

    def db_commit(self):
        try:
            db.session.commit()
        except sqlalchemy_exc.IntegrityError:
            current_app.logger.exception("Integrety error adding {}".format(self))
            db.session.rollback()

    @classmethod
    def create(model_class, **kwargs):
        new_obj = model_class()
        for key, value in kwargs.items():
            if hasattr(new_obj, key):
                setattr(new_obj, key, value)
                current_app.logger.debug("Set new obj <{}> attr {} to {}.".format(
                    model_class, key, value
                ))
            else:
                current_app.logger.debug("Model <{}> has no attribute {}.".format(
                    model_class, key
                ))

        new_obj.save_to_db()
        return new_obj

    @classmethod
    def get_count(model_class):
        query = model_class.query
        count_query = query.statement.with_only_columns([sqlalchemy_func.count()]).order_by(None)
        count = query.session.execute(count_query).scalar()
        return count


class BaseUser(UserMixin, BaseMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False, info={'label': 'E-Mail'})
    username = db.Column(db.String(40), unique=True, nullable=False, info={'label': 'Username'})
    password = db.Column(db.String(100), primary_key=False, unique=False,
                         nullable=False, info={'label': 'Password'})
    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    last_login = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    # is_admin = db.Column(db.Boolean, index=False, unique=False, nullable=False)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_student(self):
        return False

    @property
    def is_teacher(self):
        return False

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(
            password,
            method='sha256'
        )

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def activate_user(self):
        self.is_activated = True
        self.db_commit()

    def add_to_db(self):
        self.created_on = datetime.now()
        db.session.add(self)
        self.db_commit()
