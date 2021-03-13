from django.test import TestCase

from .. import admin
from ..models import User, Teacher
from .test_view_teachers import create_course

class TeacherAdminTest(TestCase):
    def setUp(self):
        su = User.objects.create_superuser('test@test.de', 'password123', is_teacher=True)
        self.teacher = Teacher.objects.create(
            user=su
        )
        self.teacher.save()
        self.course = create_course()
        self.teacher.courses.add(self.course)

    def test_courses_display(self):
        self.client.force_login(self.teacher.user)

        ta = admin.TeacherAdmin(Teacher, self.client)
        self.assertEqual(ta.courses_display(self.teacher), self.course.name)
