from flask_assets import Environment, Bundle


def compile_assets(app):
    assets = Environment(app)

    js = Bundle(
        'js/*.js',  # 'home_bp/js/*.js', 'admin_bp/js/*.js',
        filters='jsmin', output='gen/packed.js'
    )
    css = Bundle(
        'css/*.css',
        # 'home_bp/css/*.css', 'auth_bp/css/*.css',
        filters='cssmin', output='gen/packed.css'
    )
    home_css = Bundle('home_bp/css/*.css', filters='cssmin', output='gen/home_packed.css')

    bundles = {
        'js_all': js,
        'css_all': css,
        'home_css': home_css,
    }

    # selinux prevents flask-assets to dynamically build/access cached files
    if app.config['DISABLE_CACHE']:
        assets.cache = False
        assets.manifest = False

    assets.register(bundles)
    # assets.register('css_all', css)
    return assets
