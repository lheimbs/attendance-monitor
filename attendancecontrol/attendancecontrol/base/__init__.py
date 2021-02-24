from flask import Blueprint, redirect, url_for

# Blueprint Configuration
base_bp = Blueprint(
    'base_bp', __name__,
)


@base_bp.route('/')
def base():
    """ home page with basic infos """
    return redirect(url_for('home_bp.home'))
