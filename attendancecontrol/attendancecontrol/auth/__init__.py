# from functools import wraps
from datetime import datetime

from flask import flash, redirect, url_for, render_template, request, Blueprint
# , current_app
from flask_login import current_user, login_user, login_required, logout_user, LoginManager
# from flask_login.config import EXEMPT_METHODS

from ..models.models import Student
from ..models.models import Teacher
from .forms import LoginForm, StudentSignupForm, TeacherSignupForm
from .Login_Manager import MyAnonymousUser


login_manager = LoginManager()


def init_login(app):
    """ initiate login manager with custom anonymoususer class """
    login_manager.anonymous_user = MyAnonymousUser
    login_manager.init_app(app)


# Blueprint Configuration
auth_bp = Blueprint(
    'auth_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Log-in page for registered students.

    GET requests serve Log-in page.
    POST requests validate and redirect user to dashboard.
    """
    STUDENT_URL = url_for('student_bp.student')
    TEACHER_URL = url_for('teacher_bp.teacher')

    # Bypass if user is logged in
    if current_user.is_authenticated:
        # if hasattr(current_user, 'first_name'):
        #     url = TEACHER_URL
        # elif hasattr(current_user, 'mac'):
        #     url = STUDENT_URL
        if current_user.is_teacher:
            url = TEACHER_URL
        elif current_user.is_student:
            url = STUDENT_URL
        else:
            url = url_for('home_bp.home')
        return redirect(url)

    form = LoginForm()
    # # Validate login attempt
    if form.validate_on_submit():
        student = Student.query.filter_by(username=form.username.data).first()
        teacher = Teacher.query.filter_by(username=form.username.data).first()

        if student:
            user = student
            url = STUDENT_URL
        elif teacher:
            user = teacher
            url = TEACHER_URL
        else:
            user = None

        if user and user.check_password(password=form.password.data):
            logged_in = login_user(user, remember=form.remember_me.data)
            if logged_in:  # Log in as newly created user
                user.last_login = datetime.now()
                user.db_commit()
            next_page = request.args.get('next')
            return redirect(next_page or url)
        flash('Invalid username/password combination', 'error')
        return redirect(url_for('auth_bp.login'))
    return render_template(
        'login.html',
        form=form,
        title='Log in.',
        template='login-page',
        body="Log in with your User account."
    )


@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    form = StudentSignupForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        mat_nr = form.mat_nr.data
        mac = form.mac.data

        existing_user = Student.query.filter_by(username=username).first()
        existing_user_email = Student.query.filter_by(email=email).first()
        if existing_user is not None:
            flash('A user already exists with that username.', 'error')
        elif existing_user_email is not None:
            flash('A user already exists with that email.', 'error')
        else:
            user = Student.create(
                username=username,
                email=email,
                mat_nr=mat_nr,
                mac=mac
            )
            user.set_password(form.password.data)
            user.db_commit()
            if login_user(user):  # Log in as newly created user
                user.last_login = datetime.now()
                user.db_commit()
            return redirect(url_for('student_bp.student'))
    return render_template(
        'register.html',
        title='Create a Student-Account.',
        form=form,
        template='register-page',
        body="Sign up for a user account."
    )


@auth_bp.route('/register/teacher', methods=['GET', 'POST'])
def register_teacher():
    form = TeacherSignupForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        existing_user = Teacher.query.filter_by(username=username).first()
        existing_user_email = Teacher.query.filter_by(email=email).first()
        if existing_user is not None:
            flash('A user already exists with that username.', 'error')
        elif existing_user_email is not None:
            flash('A user already exists with that email.', 'error')
        else:
            user = Teacher.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            user.set_password(password)
            user.add_to_db()
            if login_user(user):  # Log in as newly created user
                user.last_login = datetime.now()
                user.db_commit()
            return redirect(url_for('teacher_bp.teacher'))
    return render_template(
        'register.html',
        title='Create a Teacher-Account.',
        form=form,
        template='register-page',
        body="Sign up for a user account."
    )


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home_bp.home'))


@login_manager.user_loader
def load_user(user_id):
    """Check if user is logged-in on every page load."""
    if user_id is not None:
        student = Student.query.get(user_id)
        teacher = Teacher.query.get(user_id)
        return student or teacher
    return None


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash('You must be logged in to view that page.', 'error')
    return redirect(url_for('auth_bp.login'))
