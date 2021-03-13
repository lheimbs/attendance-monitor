from .models import Student, Teacher


def get_users_courses_ongoing_states(user_object):
    courses = {}
    if isinstance(user_object, Student):
        for course in user_object.courses.all():
            courses[course.id] = True if course.is_ongoing() else False
    elif isinstance(user_object, Teacher):
        for course in user_object.courses.all():
            courses[course.id] = True if course.is_ongoing() else False
        for course in user_object.additional_courses.all():
            courses[course.id] = True if course.is_ongoing() else False
    return courses
