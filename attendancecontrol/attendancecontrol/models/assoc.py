from . import db

association_table = db.Table(
    'association',
    db.Column('courses_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
    db.Column('students_id', db.Integer, db.ForeignKey('students.id'), primary_key=True)
)

days_association_table = db.Table(
    'days_association',
    db.Column('courses_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
    db.Column('coursedays_id', db.Integer, db.ForeignKey('coursedays.id'), primary_key=True)
)
