import enum

from . import db
from .base import BaseMixin, BaseUserMixin
from .assoc import association_table, days_association_table

class Weekdays(enum.Enum):
    monday = 1
    tuesday = 2
    wednesday = 3
    thursday = 4
    friday = 5
    saturday = 6
    sunday = 7


class CourseDay(db.Model, BaseMixin):
    __tablename__ = 'coursedays'

    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Enum(Weekdays), nullable=False)
    time = db.Column(db.Time, nullable=False)

    courses = db.relationship(
        "Course",
        secondary=days_association_table,
        back_populates="days"
    )


class Course(db.Model, BaseMixin):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    uuid = db.Column(db.String)
    min_attend_time = db.Column(db.Integer)
    duration = db.Column(db.Interval)

    days = db.relationship(
        'CourseDay',
        secondary=days_association_table,
        back_populates="courses"
    )
    students = db.relationship(
        'Student',
        secondary=association_table,
        back_populates="courses"
    )
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))


class Teacher(db.Model, BaseUserMixin):
    __tablename__ = 'teachers'

    first_name = db.Column(db.String, nullable=False, info={'label': 'First Name'})
    last_name = db.Column(db.String, nullable=False, info={'label': 'Last Name'})

    courses = db.relationship("Course")

    @property
    def is_teacher(self):
        return True


class Student(db.Model, BaseUserMixin):
    __tablename__ = 'students'

    mat_nr = db.Column(db.Integer, nullable=False, unique=True, info={'label': 'Matrikel Nr.'})
    mac = db.Column(db.String(12), info={'label': "Your mobile device's MAC-Adress"})

    courses = db.relationship(
        'Course',
        secondary=association_table,
        back_populates="students"
    )

    @property
    def is_student(self):
        return True
