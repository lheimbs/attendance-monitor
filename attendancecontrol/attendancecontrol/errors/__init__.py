from flask import render_template
from flask_wtf.csrf import CSRFError


def register_handlers(app):
    # if app.config.get('DEBUG') is True:
    #     app.logger.debug('Skipping error handlers in Debug mode')
    #     return

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        app.logger.error(f"CSRF Error: {error.description}")
        return render_template(
            "errors/error.html", title="Error 400", error_code="400",
            error_msg="Sheit, I think you need to reload this... or it is broken >.<"
        ), 400
        # return jsonify(error.description), 400

    @app.errorhandler(401)
    def unauthorized(*args, **kwargs):
        # do stuff
        return render_template(
            "errors/error.html", title="Error 401", error_code="401",
            error_msg="Fuck, you sadly don't have access to this :'("
        ), 403

    @app.errorhandler(403)
    def forbidden_page(*args, **kwargs):
        # do stuff
        return render_template(
            "errors/error.html", title="Error 403", error_code="403",
            error_msg="Bummer, it seems like your don't have access to this page :("
        ), 403

    @app.errorhandler(404)
    def page_not_found(*args, **kwargs):
        # do stuff
        return render_template(
            "errors/error.html", title="Error 404", error_code="404",
            error_msg="Damn, this page or w/e does not seem to exist :/"
        ), 404

    @app.errorhandler(410)
    def page_gone(*args, **kwargs):
        # do stuff
        return render_template(
            "errors/error.html", title="Error 410", error_code="410",
            error_msg="Oh man, this page is gone for good... Maybe try another one?"
        ), 410

    @app.errorhandler(500)
    def server_error_page(*args, **kwargs):
        # do stuff
        return render_template(
            "errors/error.html", title="Error 500", error_code="500",
            error_msg="Yikes, this one is on me. I must have fucked up the programming or something :("
        ), 500

    @app.errorhandler(501)
    def server_error_not_implemented(*args, **kwargs):
        # do stuff
        return render_template(
            "errors/error.html", title="Error 501", error_code="501",
            error_msg="Ugh, it seem like I forgot to implement something...Sorryyyyyy"
        ), 501
