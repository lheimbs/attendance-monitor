from django.test import TestCase
from django.utils import timezone

from .. import utils
from ..models import User
from .test_view_teachers import create_teacher, create_course
from .test_view_students import create_student

class UtilsTest(TestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.student = create_student()
        self.user = User.objects.create_user('test@test.de', 'passwordistoolong')
        self.course = create_course()

    def test_teacher_queries_courses_states_with_one_course(self):
        self.teacher.courses.add(self.course)
        self.assertDictEqual(utils.get_users_courses_ongoing_states(self.teacher), {self.course.id: False})

    def test_non_teacher_student_queries_courses_states(self):
        self.assertDictEqual(utils.get_users_courses_ongoing_states(self.user), {})

    def test_student_query_show_correct_course(self):
        self.student.courses.add(self.course, through_defaults={'created': timezone.now(), 'modified': timezone.now()})
        self.assertDictEqual(
            utils.get_users_courses_ongoing_states(self.student), {self.course.id: False}
        )

    def test_teacher_query_shows_additional_course(self):
        self.teacher.additional_courses.add(self.course)
        self.assertDictEqual(utils.get_users_courses_ongoing_states(self.teacher), {self.course.id: False})
