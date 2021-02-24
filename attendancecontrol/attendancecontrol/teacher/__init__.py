from flask import Blueprint, render_template

# Blueprint Configuration
teacher_bp = Blueprint(
    'teacher_bp', __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/teacher/'
)


@teacher_bp.route('/')
def teacher():
    """ home page with basic infos """
    return render_template('teacher.html', title="Teacher")
