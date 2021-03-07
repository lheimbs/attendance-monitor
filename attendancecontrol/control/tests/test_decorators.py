from django.http.response import HttpResponse
from django.views import View
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils.decorators import method_decorator

from .. import models
from ..decorators import student_required, teacher_required

USER_EMAIL = 'user@test.com'
TEACHER_EMAIL = 'teacher@test.com'
STUDENT_EMAIL = 'student@test.com'

class TeacherRequiredTest(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(email=USER_EMAIL, username=USER_EMAIL, password='mytestpassword')
        self.teacher = models.Teacher.objects.create(
            user=models.User.objects.create(
                email=TEACHER_EMAIL, username=TEACHER_EMAIL,
                password='mytestpassword', is_teacher=True
            )
        )
        self.student = models.Student.objects.create(
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
        @teacher_required
        def a_view(request):
            return HttpResponse()
        request = self.factory.get(reverse('home'))
        request.user = self.teacher.user
        response = a_view(request)
        self.assertEqual(response.status_code, 200)

    def test_teacher_required_decorator_redirects_student(self):
        """teacher_required redirects student to login view"""
        @teacher_required
        def a_view(request):
            return HttpResponse()
        request = self.factory.get(reverse('home'))
        request.user = self.student.user
        response = a_view(request)
        self.assertEqual(response.status_code, 302)

    def test_teacher_required_decorator_redirects_non_teacher_user(self):
        """teacher_required redirects non-student user to login view"""
        @teacher_required
        def a_view(request):
            return HttpResponse()
        request = self.factory.get(reverse('home'))
        request.user = self.user
        response = a_view(request)
        self.assertEqual(response.status_code, 302)

    def test_teacher_decorator_with_class_based_view(self):
        @method_decorator([teacher_required], name='dispatch')
        class MyView(View):
            def get(self, request, *args, **kwargs):
                return HttpResponse('Hello, World!')
        request = self.factory.get('/')
        request.user = self.teacher.user
        response = MyView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_teacher_decorator_None_function(self):
        def a_view(request):
            teacher_required(None)
            return HttpResponse()
        request = self.factory.get('/')
        request.user = self.teacher.user
        response = a_view(request)
        self.assertEqual(response.status_code, 200)


class StudentRequiredTest(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(email=USER_EMAIL, username=USER_EMAIL, password='mytestpassword')
        self.teacher = models.Teacher.objects.create(
            user=models.User.objects.create(
                email=TEACHER_EMAIL, username=TEACHER_EMAIL,
                password='mytestpassword', is_teacher=True
            )
        )
        self.student = models.Student.objects.create(
            student_nr=1,
            mac="112233445566",
            user=models.User.objects.create(
                email=STUDENT_EMAIL, username=STUDENT_EMAIL,
                password='mytestpassword', is_student=True
            )
        )
        self.factory = RequestFactory()

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

    def test_student_decorator_with_class_based_view(self):
        @method_decorator([student_required], name='dispatch')
        class MyView(View):
            def get(self, request, *args, **kwargs):
                return HttpResponse('Hello, World!')
        request = self.factory.get('/')
        request.user = self.student.user
        response = MyView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_student_decorator_None_function(self):
        def a_view(request):
            student_required(None)
            return HttpResponse()
        request = self.factory.get('/')
        request.user = self.student.user
        response = a_view(request)
        self.assertEqual(response.status_code, 200)
