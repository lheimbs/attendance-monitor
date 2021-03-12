from django.test import TestCase

from .. import utils
from ..models import User
from .test_view_teachers import create_teacher, create_course

class UtilsTest(TestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.user = User.objects.create_user('test@test.de', 'passwordistoolong')
        self.course = create_course()

    def test_teacher_queries_courses_states_with_one_course(self):
        self.teacher.courses.add(self.course)
        self.assertDictEqual(utils.get_users_courses_ongoing_states(self.teacher), {self.course.id: False})

    def test_non_teacher_student_queries_courses_states(self):
        self.assertDictEqual(utils.get_users_courses_ongoing_states(self.user), {})
