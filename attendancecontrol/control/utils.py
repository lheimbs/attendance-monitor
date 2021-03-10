from .models import Student, Teacher


def get_users_courses_ongoing_states(user_object):
    if not isinstance(user_object, Student) and not isinstance(user_object, Teacher):
        return {}

    courses = {}
    for course in user_object.courses.all():
        courses[course.id] = True if course.is_ongoing() else False
    return courses
