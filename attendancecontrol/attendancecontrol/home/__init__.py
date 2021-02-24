from flask import Blueprint, render_template

# Blueprint Configuration
home_bp = Blueprint(
    'home_bp', __name__,
    template_folder='templates',
    static_folder='static',
    # static_url_path='/static/home'
)


@home_bp.route('/home')
def home():
    """ home page with basic infos """
    return render_template(
        'home.html',
        title='Home',
        template='home-page',
        body="Homepage."
    )
