from django.http.response import HttpResponse
from django.test import TestCase, RequestFactory
from django.urls import reverse

from .. import models
from ..decorators import student_required, teacher_required

USER_EMAIL = 'user@test.com'
TEACHER_EMAIL = 'teacher@test.com'
STUDENT_EMAIL = 'student@test.com'

class DecoratorsTest(TestCase):
    def setUp(self):
        models.User.objects.create(email=USER_EMAIL, username=USER_EMAIL, password='mytestpassword')
        models.Teacher.objects.create(
            user=models.User.objects.create(
                email=TEACHER_EMAIL, username=TEACHER_EMAIL,
                password='mytestpassword', is_teacher=True
            )
        )
        models.Student.objects.create(
            student_nr=1,
            mac="112233445566",
            user=models.User.objects.create(
                email=STUDENT_EMAIL, username=STUDENT_EMAIL,
                password='mytestpassword', is_student=True
            )
        )

        self.factory = RequestFactory()

    def test_teacher_required_decorator_allows_teacher(self):
        """teacher_required allows teacher access to view"""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        @teacher_required
        def a_view(request):
            return HttpResponse()
        request = self.factory.get(reverse('home'))
        request.user = teacher.user
        response = a_view(request)
        self.assertEqual(response.status_code, 200)

    def test_teacher_required_decorator_forbids_student(self):
        """teacher_required redirects student to login view"""
        student = models.Student.objects.get(user__email=STUDENT_EMAIL)
        @teacher_required
        def a_view(request):
            return HttpResponse()
        request = self.factory.get(reverse('home'))
        request.user = student.user
        response = a_view(request)
        self.assertEqual(response.status_code, 302)

    def test_teacher_required_decorator_forbids_non_teacher_user(self):
        """teacher_required redirects non-student user to login view"""
        user = models.User.objects.get(email=USER_EMAIL)
        @teacher_required
        def a_view(request):
            return HttpResponse()
        request = self.factory.get(reverse('home'))
        request.user = user
        response = a_view(request)
        self.assertEqual(response.status_code, 302)
        # self.assert(response.url, )

    def test_student_required_decorator_allows_student(self):
        """student_required allows student access to view"""
        student = models.Student.objects.get(user__email=STUDENT_EMAIL)
        @student_required
        def a_view(request):
            return HttpResponse()
        request = self.factory.get(reverse('home'))
        request.user = student.user
        response = a_view(request)
        self.assertEqual(response.status_code, 200)

    def test_student_required_decorator_forbids_teacher(self):
        """student_required redirects teacher to login view"""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        @student_required
        def a_view(request):
            return HttpResponse()
        request = self.factory.get(reverse('home'))
        request.user = teacher.user
        response = a_view(request)
        self.assertEqual(response.status_code, 302)

    def test_student_required_decorator_forbids_non_student_user(self):
        """student_required redirects non-student user to login view"""
        user = models.User.objects.get(email=USER_EMAIL)
        @student_required
        def a_view(request):
            return HttpResponse()
        request = self.factory.get(reverse('home'))
        request.user = user
        response = a_view(request)
        self.assertEqual(response.status_code, 302)
