"""Sign-up & log-in forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms_components import EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length
# from wtforms_alchemy import ModelForm
from wtforms_alchemy import model_form_factory

# The variable db here is a SQLAlchemy object instance from
# Flask-SQLAlchemy package
from ..models import db
from ..models.models import Student
from ..models.models import Teacher


BaseModelForm = model_form_factory(FlaskForm)

class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session

    email = EmailField(validators=[DataRequired(), Email()])
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=6, message='Select a stronger password.')
        ]
    )
    confirm = PasswordField(
        'Confirm Your Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match.')
        ]
    )


class StudentSignupForm(ModelForm):
    class Meta:
        model = Student
        exclude = ['created_on', 'last_login']
    # submit = SubmitField('Register')


class TeacherSignupForm(ModelForm):
    class Meta:
        model = Teacher
        exclude = ['created_on', 'last_login']
    # submit = SubmitField('Register')


class SignupForm(FlaskForm):
    """User Sign-up Form."""
    name = StringField(
        'Name',
        validators=[DataRequired()]
    )
    email = StringField(
        'Email',
        validators=[
            Length(min=6),
            Email(message='Enter a valid email.'),
            DataRequired()
        ]
    )
    username = StringField(
        'Username',
        validators=[
            Length(min=6),
            DataRequired()
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=6, message='Select a stronger password.')
        ]
    )
    confirm = PasswordField(
        'Confirm Your Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match.')
        ]
    )
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    """User Log-in Form."""
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
        ]
    )
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log In')
