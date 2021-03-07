from django.test import TestCase
from django.urls import reverse

from .test_view_teachers import create_teacher
from .test_view_students import create_student

class TestHome(TestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.student = create_student()

    def test_home_redirect_to_teacher_courses_when_teacher_is_logged_in(self):
        self.client.force_login(self.teacher.user)
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, reverse('teacher:courses'))

    def test_home_redirect_to_student_courses_when_student_is_logged_in(self):
        self.client.force_login(self.student.user)
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, reverse('student:courses'))

    def test_home_render_home_when_nobody_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse('home'))
        self.assertContains(response, "Sign up")
        self.assertContains(response, "Login")
