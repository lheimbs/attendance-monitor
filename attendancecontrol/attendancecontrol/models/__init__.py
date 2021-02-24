from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)

    with app.app_context():
        from .assoc import days_association_table, association_table    # noqa: F401
        # from .course import Course      # noqa: F401
        # from .student import Student    # noqa: F401
        # from .teacher import Teacher    # noqa: F401
        # from .days import Weekdays      # noqa: F401
        from .models import CourseDay, Course, Student, Teacher     # noqa: F401

        if app.config['DROP_ALL']:
            app.logger.debug("Drop all Database Tables")
            db.drop_all()
        db.create_all()
