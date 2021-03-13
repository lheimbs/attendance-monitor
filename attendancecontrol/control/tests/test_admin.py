from django.test import TestCase
from django.urls.base import reverse
from django.utils import timezone
from django.forms.models import model_to_dict

from .. import admin
from ..admin import forms
from .. import models
from .test_view_teachers import create_course, create_teacher


class TeacherAdminTest(TestCase):
    def setUp(self):
        su = models.User.objects.create_superuser('test@test.de', 'password123', is_teacher=True)
        self.teacher = models.Teacher.objects.create(
            user=su
        )
        self.teacher.save()
        self.course = create_course()
        self.teacher.courses.add(self.course)

    def test_courses_display(self):
        self.client.force_login(self.teacher.user)

        ta = admin.TeacherAdmin(models.Teacher, self.client)
        self.assertEqual(ta.courses_display(self.teacher), self.course.name)


class StudentAdminFormTest(TestCase):
    def setUp(self):
        su = models.User.objects.create_superuser('test@test.de', 'password123', is_teacher=True)
        self.teacher = models.Teacher.objects.create(
            user=su
        )
        self.course = create_course()
        self.student = models.Student.objects.create(
            user=models.User.objects.create(
                email="teststudent@test.de",
                username="teststudent@test.de",
                is_student=True,
            ),
            student_nr=123,
            mac="112233445566"
        )
        self.client.force_login(self.teacher.user)

    def test_student_admin_form_can_get(self):
        student_url = reverse('admin:control_student_change', args=[self.student.user.id])
        response = self.client.get(student_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Courses:')

    def test_student_admin_form_has_user(self):
        form = forms.StudentAdminForm(instance=self.student, data=model_to_dict(self.student))
        new_student = form.save(commit=True)
        self.assertEqual(new_student.pk, self.student.pk)

    def test_student_admin_form_assigns_user(self):
        new_user = models.User.objects.create(
            email="teststudent_2@test.de",
            username="teststudent_2@test.de",
            is_student=True,
        )

        student_data = model_to_dict(self.student)
        student_data['user'] = new_user.id
        form = forms.StudentAdminForm(data=student_data)
        new_student = form.save(commit=True)
        self.assertEqual(new_student.user.email, new_user.email)

    def test_student_admin_form_does_not_commit___(self):
        student_data = model_to_dict(self.student)
        form = forms.StudentAdminForm(instance=self.student, data=student_data)
        new_student = form.save()
        self.assertQuerysetEqual(new_student.courses.all(), [])

    def test_student_admin_form_does_not_commit(self):
        some_user = models.User.objects.create(
            email="teststudent_2@test.de",
            username="teststudent_2@test.de",
            is_student=True,
        )
        student_data = {'student_nr': 12, 'mac': '112233445566', 'user': some_user.pk, 'courses': []}
        form = forms.StudentAdminForm()
        form.data = student_data
        new_student = form.save(commit=False)
        self.assertFalse(hasattr(new_student, 'user'))


class CourseAdminFormTest(TestCase):
    def setUp(self) -> None:
        self.course = create_course()
        self.teacher = create_teacher()

    def test_form_init_with_instance(self):
        form = forms.CourseAdminForm(instance=self.course)
        self.assertIn(self.course.name, str(form))

    def test_form_init_without_instance(self):
        form = forms.CourseAdminForm()
        self.assertNotIn(self.course.name, str(form))

    def test_form_init_with_teacher_set(self):
        self.course.teacher = self.teacher
        self.course.save()
        form = forms.CourseAdminForm(instance=self.course)
        self.assertQuerysetEqual(form.fields['additional_teachers'].choices.queryset, [])

    def test_save_form_with_additonal_teacher(self):
        self.teacher_su = models.Teacher.objects.create(
            user=models.User.objects.create_superuser('test@test.de', 'password123', is_teacher=True)
        )
        self.course.teacher = self.teacher_su
        course_data = model_to_dict(self.course)
        course_data['additional_teachers'] = [self.teacher]
        form = forms.CourseAdminForm(instance=self.course, data=course_data)
        new_course = form.save()
        self.assertEqual(new_course.additional_teachers.last(), self.teacher)

    def test_save_form_with_commit_false_and_no_course_pk(self):
        course_data = model_to_dict(self.course)
        course_data['teacher'] = self.teacher
        form = forms.CourseAdminForm()
        form.data = course_data
        new_course = form.save(commit=False)
        self.assertIsNone(new_course.pk)
