from django.test import TestCase
from .. import models, forms

TEACHER_EMAIL = 'teacher@test.com'
STUDENT_EMAIL = 'student@test.com'

class TeacherSignUpFormTest(TestCase):
    def test_teacher_form_saves_teacher_object(self):
        form = forms.TeacherSignUpForm({
            'email': TEACHER_EMAIL,
            'first_name': 'first',
            'last_name': 'last',
            'password1': 'mytestpassword',
            'password2': 'mytestpassword',
        })
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(models.Teacher.objects.last().user.email, TEACHER_EMAIL)
        self.assertEqual(models.Teacher.objects.last().user.username, TEACHER_EMAIL)
        self.assertEqual(models.Teacher.objects.last().user.first_name, 'first')
        self.assertEqual(models.Teacher.objects.last().user.last_name, 'last')
        self.assertTrue(models.Teacher.objects.last().user.is_teacher)

class StudentSignUpFormTest(TestCase):
    def test_student_form_saves_student_object(self):
        form = forms.StudentSignUpForm({
            'email': STUDENT_EMAIL,
            'student_nr': 123,
            'mac': '112233445566',
            'password1': 'mytestpassword',
            'password2': 'mytestpassword',
        })
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(models.Student.objects.last().user.email, STUDENT_EMAIL)
        self.assertEqual(models.Student.objects.last().user.username, STUDENT_EMAIL)
        self.assertTrue(models.Student.objects.last().user.is_student)
        self.assertEqual(models.Student.objects.last().student_nr, 123)
        self.assertEqual(models.Student.objects.last().mac, '112233445566')
