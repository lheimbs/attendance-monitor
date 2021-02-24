from flask import Blueprint, render_template
from flask_login import login_required

# Blueprint Configuration
student_bp = Blueprint(
    'student_bp', __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/student/'
)


@login_required
@student_bp.route('/')
def student():
    """ home page with basic infos """
    return render_template('student.html', title="Student")
