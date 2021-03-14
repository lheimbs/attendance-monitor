import itertools
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages

from .. import models
from ..views import students as students_view

STUDENT_EMAIL = 'student@test.com'

# Make now() a constant
NOW_FOR_TESTING = timezone.make_aware(
    timezone.datetime(2021, 3, 1, 10, 0, 0, 0),  # 1.3.2021 was a monday
    timezone.utc
)
NOW_FUTURE_FOR_TESTING = timezone.make_aware(
    timezone.datetime(2021, 3, 2, 9, 55, 0, 0),
    timezone.utc
)


def create_student(custom_email=""):
    student, _ = models.Student.objects.get_or_create(
        user=models.User.objects.create(
            email=custom_email if custom_email else STUDENT_EMAIL,
            username=custom_email if custom_email else STUDENT_EMAIL,
            is_student=True,
        ),
        student_nr=123,
        wifi_info=models.WifiInfo.objects.create(
            mac="112233445566"
        )
    )
    return student


def create_weekdays(num=5):
    time = 7  # hour in the day
    time_increment = 60  # minutes
    days = itertools.cycle(models.WeekDayChoices.values)
    weekdays = []
    for _ in range(num):
        day = next(days)
        day_time = timezone.now().replace(hour=time) + timezone.timedelta(minutes=time_increment)
        time = (time + 1) if time < 20 else 7
        weekday = models.WeekDay.objects.create(day=models.WeekDayChoices(day), time=day_time.time())
        weekdays.append(weekday)
    return weekdays


def create_course(num_weekdays):
    course = models.Course.objects.create(name='test_course_edit')
    for weekday in create_weekdays(num_weekdays):
        course.start_times.add(weekday)
    return course


class StudentSignUpViewTest(TestCase):
    def test_post_student(self):
        """Verify that student object is created and the user's is_student set to true"""
        self.client.post(reverse('student_signup'), data={
            'email': STUDENT_EMAIL, 'student_nr': '1234', 'mac': '112233445566',
            'password1': 'mytestpassword', 'password2': 'mytestpassword'
        })
        self.assertEqual(models.Student.objects.last().user.email, STUDENT_EMAIL)
        self.assertIs(models.Student.objects.last().user.is_student, True)

    def test_usertype_student_in_context(self):
        """Test if user_type=student is present in view context"""
        response = self.client.get(reverse('student_signup'))
        self.assertDictContainsSubset({'user_type': 'student'}, response.context)


class StudentEditTest(TestCase):
    def setUp(self):
        self.student = create_student()

    def test_correct_redirect_of_successful_edit(self):
        self.client.force_login(self.student.user)

        response = self.client.post(reverse('student:edit_account', args=(self.student.user.id,)), data={
            'email': self.student.user.email+'e', 'student_nr': '456', 'mac': 'aabbccddeeff'
        })
        self.assertRedirects(response, reverse('student:courses'))

    def test_dont_let_logged_in_student_edit_someone_elses_profile(self):
        student = create_student(custom_email=STUDENT_EMAIL+"2")
        self.client.force_login(self.student.user)

        response = self.client.post(reverse('student:edit_account', args=(student.user.id,)))
        self.assertEqual(response.status_code, 404)

    def test_student_nr_in_edit_data(self):
        self.client.force_login(self.student.user)
        response = self.client.get(reverse('student:edit_account', args=(self.student.user.id,)))
        self.assertContains(response, self.student.student_nr)

    def test_mac_in_edit_data(self):
        self.client.force_login(self.student.user)
        response = self.client.get(reverse('student:edit_account', args=(self.student.user.id,)))
        self.assertContains(response, '11:22:33:44:55:66')  # TODO: properly format mac using netaddr

    def test_empty_student_mac_in_edit_data(self):
        self.student.wifi_info = None
        self.student.save()
        self.client.force_login(self.student.user)
        response = self.client.get(reverse('student:edit_account', args=(self.student.user.id,)))
        self.assertNotContains(response, '11:22:33:44:55:66')  # TODO: properly format mac using netaddr

    def test_student_data_actually_changed(self):
        self.client.force_login(self.student.user)
        data = {
            'email': self.student.user.email,
            'student_nr': '111111',
            'mac': self.student.wifi_info.mac,
        }
        self.client.post(reverse('student:edit_account', args=(self.student.user.id,)), data=data)
        self.student.refresh_from_db()
        self.assertEqual(self.student.student_nr, 111111)

class StudentCoursesListTest(TestCase):
    def setUp(self):
        create_student()

    def test_no_courses(self):
        """If no courses exist for student, an appropriate message is displayed."""
        student = models.Student.objects.get(user__email=STUDENT_EMAIL)

        self.client.force_login(student.user)
        response = self.client.get(reverse('student:courses'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No courses yet...')
        self.assertQuerysetEqual(response.context['courses'], [])

    def test_non_student_course(self):
        """When student has no courses assigned to their courses relationship behave as if no courses."""
        student = models.Student.objects.get(user__email=STUDENT_EMAIL)
        models.Course.objects.create(name="testcourse")  # mock course that does not belong to student

        self.client.force_login(student.user)
        response = self.client.get(reverse('student:courses'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No courses yet...')
        self.assertQuerysetEqual(response.context['courses'], [])

    def test_student_has_course(self):
        """When student has a course assigned to their courses relationship show it on the page."""
        student = models.Student.objects.get(user__email=STUDENT_EMAIL)
        course = models.Course.objects.create(name="testcourse")
        student.courses.add(course, through_defaults={'created': timezone.now(), 'modified': timezone.now()})

        self.client.force_login(student.user)
        response = self.client.get(reverse('student:courses'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['courses'],
            ['<Course: name: testcourse, min_attend_time: 45, duration: 90>']
        )


class StudentCourseDetailTest(TestCase):
    def setUp(self):
        create_student()

    def test_show_course_that_belongs_to_student(self):
        """Show a course's details that is in the students courses relationship."""
        student = models.Student.objects.get(user__email=STUDENT_EMAIL)
        course = models.Course.objects.create(name="testcourse")
        student.courses.add(course, through_defaults={'created': timezone.now(), 'modified': timezone.now()})

        self.client.force_login(student.user)
        response = self.client.get(reverse('student:detail', args=(course.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, course.name)

    def test_error_for_course_that_does_not_belong_to_student(self):
        """Show an error for a course that is not in the students courses field."""
        student = models.Student.objects.get(user__email=STUDENT_EMAIL)
        course = models.Course.objects.create(name="testcourse")

        self.client.force_login(student.user)
        response = self.client.get(reverse('student:detail', args=(course.id,)))
        self.assertEqual(response.status_code, 404)


class AuthenticateStudentCourseTest(TestCase):
    def setUp(self):
        self.student = create_student()
        self.course = create_course(0)

    def test_student_course_exists_and_student_registered_to_course(self):
        self.student.courses.add(self.course, through_defaults={'created': timezone.now(), 'modified': timezone.now()})

        retvals = students_view.authenticate_student_course(self.course, self.student, None)
        self.assertIs(retvals[0], False)
        self.assertEqual(retvals[1], messages.INFO)
        self.assertEqual(retvals[2], "You are already registered to this course.")
        self.assertEqual(retvals[3], True)

    def test_course_has_no_access_token(self):
        retvals = students_view.authenticate_student_course(self.course, self.student, None)
        self.assertIs(retvals[0], False)
        self.assertEqual(retvals[1], messages.WARNING)
        self.assertEqual(retvals[2], "This course is not open for registrations!")
        self.assertEqual(retvals[3], False)

    def test_courses_access_token_has_expired(self):
        """Test that the access token of the course has expired"""
        with mock.patch('django.utils.timezone.now', return_value=NOW_FOR_TESTING):
            token = models.AccessToken.objects.create(valid_time=1)
        self.course.access_token = token

        with mock.patch('django.utils.timezone.now', return_value=NOW_FUTURE_FOR_TESTING):
            retvals = students_view.authenticate_student_course(self.course, self.student, token.token)
        self.assertIs(retvals[0], False)
        self.assertEqual(retvals[1], messages.WARNING)
        self.assertEqual(retvals[2], "This course is not open for registrations!")
        self.assertEqual(retvals[3], False)

    def test_supplied_token_is_invalid(self):
        """Test that the supplied token is not the token set for the course"""
        with mock.patch('django.utils.timezone.now', return_value=NOW_FOR_TESTING):
            token = models.AccessToken.objects.create(valid_time=1)
        self.course.access_token = token

        with mock.patch('django.utils.timezone.now', return_value=NOW_FOR_TESTING):
            retvals = students_view.authenticate_student_course(self.course, self.student, "WRONG_TOKEN")
        self.assertIs(retvals[0], False)
        self.assertEqual(retvals[1], messages.WARNING)
        self.assertEqual(retvals[2], "Invalid Access Token!")
        self.assertEqual(retvals[3], False)

    def test_token_is_valid_and_not_expired(self):
        with mock.patch('django.utils.timezone.now', return_value=NOW_FOR_TESTING):
            token = models.AccessToken.objects.create(valid_time=1)
        self.course.access_token = token

        with mock.patch('django.utils.timezone.now', return_value=NOW_FOR_TESTING):
            retvals = students_view.authenticate_student_course(self.course, self.student, token.token)
        self.assertIs(retvals[0], True)
        self.assertEqual(retvals[1], messages.SUCCESS)
        self.assertEqual(retvals[2], "You successfully registered for this course.")
        self.assertEqual(retvals[3], True)


class TestRegisterStudentForCourse(TestCase):
    def setUp(self):
        self.student = create_student()
        self.student.courses.clear()
        self.course = create_course(0)

    def test_course_added_to_student_with_correct_and_not_expired_token(self):
        self.client.force_login(self.student.user)
        with mock.patch('django.utils.timezone.now', return_value=NOW_FOR_TESTING):
            token = models.AccessToken.objects.create(valid_time=10)
        self.course.access_token = token
        self.course.save()
        with mock.patch('django.utils.timezone.now', return_value=NOW_FOR_TESTING+timezone.timedelta(minutes=1)):
            self.client.get(reverse('student:register_course', args=(self.course.id, token.token)))
        student = models.Student.objects.get(pk=self.student.user.id)
        self.assertIn(self.course, student.courses.all())

    def test_redirect_to_course_details(self):
        """
        If student is already in course or was successfully added,
        test that the redirect points to the courses details
        """
        self.client.force_login(self.student.user)
        self.student.courses.add(self.course, through_defaults={'created': timezone.now(), 'modified': timezone.now()})
        response = self.client.get(reverse('student:register_course', args=(self.course.id, None)))
        self.assertRedirects(response, reverse('student:detail', args=(self.course.id,)))

    def test_redirect_to_students_courses_on_fail(self):
        """Test that if registration fails, redirect to students courses overview"""
        self.client.force_login(self.student.user)
        response = self.client.get(reverse('student:register_course', args=(self.course.id, None)))
        self.assertRedirects(response, reverse('student:courses'))


class TestManualRegisterStudentForCourse(TestCase):
    def setUp(self):
        self.student = create_student()
        self.student.courses.clear()
        self.course = create_course(0)

    def test_form_in_response_on_get(self):
        self.client.force_login(self.student.user)
        response = self.client.get(reverse('student:register_course_manual'))
        self.assertIn('form', response.context)

    def test_token_field_in_response_on_get(self):
        self.client.force_login(self.student.user)
        response = self.client.get(reverse('student:register_course_manual'))
        self.assertContains(response, "Course Token")

    def test_redirect_to_register_view_on_valid_form(self):
        self.client.force_login(self.student.user)
        response = self.client.post(reverse('student:register_course_manual'), data={
            'token': '1234567890', 'id': '1'
        }, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('student:register_course', args=('1', '1234567890')))

    def test_invalid_form_data(self):
        self.client.force_login(self.student.user)
        response = self.client.post(reverse('student:register_course_manual'), data={
            'token': '1', 'id': 'asdk'
        })
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.url, reverse('student:register_course', args=('1', '1234567890')))

class TestStudentLeaveCourse(TestCase):
    def setUp(self):
        self.student = create_student()
        self.student.courses.clear()
        self.course = create_course(0)

    def test_non_existent_course(self):
        self.client.force_login(self.student.user)
        response = self.client.get(reverse('student:leave_course', args=(123,)))
        self.assertEqual(response.status_code, 404)

    def test_student_not_in_course(self):
        self.client.force_login(self.student.user)
        response = self.client.get(reverse('student:leave_course', args=(self.course.id,)))
        self.assertEqual(response.status_code, 404)

    def test_successful_quit(self):
        self.student.courses.add(self.course, through_defaults={'created': timezone.now(), 'modified': timezone.now()})
        self.client.force_login(self.student.user)
        self.client.get(reverse('student:leave_course', args=(self.course.id,)))
        student = models.Student.objects.get(pk=self.student.user.id)
        self.assertNotIn(self.course, student.courses.all())


class GetCoursesStatesTest(TestCase):
    def setUp(self):
        self.student = create_student()
        self.course = create_course(0)

    def test_empty_dict_when_student_has_no_courses(self):
        self.client.force_login(self.student.user)
        response = self.client.get(reverse('student:courses_status'))
        self.assertJSONEqual(str(response.content, encoding='utf8'), {})

    @mock.patch('django.utils.timezone.now', return_value=NOW_FOR_TESTING)
    def test_course_not_ongoing(self, *args):
        self.course.start_times.create(
            day=models.WeekDayChoices.FRIDAY,
            time=timezone.now().replace(hour=9, minute=0, second=0, microsecond=0).time()
        )
        self.student.courses.add(self.course, through_defaults={'created': timezone.now(), 'modified': timezone.now()})
        self.student.refresh_from_db()
        self.client.force_login(self.student.user)
        response = self.client.get(reverse('student:courses_status'))
        self.assertJSONEqual(str(response.content, encoding='utf8'), {str(self.course.id): False})

    @mock.patch('django.utils.timezone.now', return_value=NOW_FOR_TESTING)
    def test_course_ongoing(self, *args):
        self.course.start_times.create(
            day=models.WeekDayChoices.MONDAY,
            time=timezone.now().time()
        )
        self.student.courses.add(self.course, through_defaults={'created': timezone.now(), 'modified': timezone.now()})
        self.student.refresh_from_db()
        self.client.force_login(self.student.user)
        response = self.client.get(reverse('student:courses_status'))
        self.assertJSONEqual(str(response.content, encoding='utf8'), {str(self.course.id): True})
