import itertools
from unittest import mock

from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import timezone
from django.urls import reverse

from .. import models
from ..views import teachers as teachers_view

USER_EMAIL = 'user@test.com'
TEACHER_EMAIL = 'teacher@test.com'
STUDENT_EMAIL = 'student@test.com'
NOW_FOR_TESTING = timezone.make_aware(
    timezone.datetime(2021, 3, 1, 10, 0, 0, 0),  # 1.3.2021 was a monday
    timezone.utc
)

def create_teacher(custom_email=""):
    teacher, _ = models.Teacher.objects.get_or_create(user=models.User.objects.create(
        first_name='first', last_name='last',
        email=custom_email if custom_email else TEACHER_EMAIL,
        username=custom_email if custom_email else TEACHER_EMAIL,
        is_teacher=True,
    ))
    return teacher


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


def create_course(num_weekdays=0):
    course = models.Course.objects.create(name='test_course_edit')
    weekdays = create_weekdays(num_weekdays)
    for weekday in weekdays:
        course.start_times.add(weekday)
    return course


class TeacherSignUpViewTest(TestCase):
    def test_post_teacher(self):
        """Verify that teacher object is created and the user's is_teacher set to true"""
        self.client.post(reverse('teacher_signup'), data={
            'email': TEACHER_EMAIL, 'first_name': 'first', 'last_name': 'last',
            'password1': 'mytestpassword', 'password2': 'mytestpassword'
        })
        self.assertEqual(models.Teacher.objects.last().user.email, TEACHER_EMAIL)
        self.assertIs(models.Teacher.objects.last().user.is_teacher, True)

    def test_usertype_teacher_in_context(self):
        """Test if user_type=teacher is present in view context"""
        response = self.client.get(reverse('teacher_signup'))
        self.assertDictContainsSubset({'user_type': 'teacher'}, response.context)


class TeacherCoursesListTest(TestCase):
    def setUp(self):
        create_teacher()

    def test_no_courses(self):
        """If no courses exist for teacher, an appropriate message is displayed."""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)

        self.client.force_login(teacher.user)
        response = self.client.get(reverse('teacher:courses'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No courses yet...')
        self.assertQuerysetEqual(response.context['courses'], [])

    def test_non_teacher_course(self):
        """When teacher has no courses assigned to their courses relationship behave as if no courses."""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        models.Course.objects.create(name="testcourse")  # mock course that does not belong to teacher

        self.client.force_login(teacher.user)
        response = self.client.get(reverse('teacher:courses'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No courses yet...')
        self.assertQuerysetEqual(response.context['courses'], [])

    def test_teacher_has_course(self):
        """When teacher has a course assigned to their courses relationship show it on the page."""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        course = models.Course.objects.create(name="testcourse")
        teacher.courses.add(course)

        self.client.force_login(teacher.user)
        response = self.client.get(reverse('teacher:courses'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['courses'],
            ['<Course: name: testcourse, min_attend_time: 45, duration: 90>']
        )


class TeacherCourseDetailTest(TestCase):
    def setUp(self):
        create_teacher()

    def test_show_course_that_belongs_to_teacher(self):
        """Show a course's details that is in the teachers courses relationship."""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        course = models.Course.objects.create(name="testcourse")
        teacher.courses.add(course)

        self.client.force_login(teacher.user)
        response = self.client.get(reverse('teacher:detail', args=(course.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, course.name)

    def test_error_for_course_that_does_not_belong_to_teacher(self):
        """Show an error for a course that is not in the teachers courses field."""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        course = models.Course.objects.create(name="testcourse")

        self.client.force_login(teacher.user)
        response = self.client.get(reverse('teacher:detail', args=(course.id,)))
        self.assertEqual(response.status_code, 404)


class TeacherAdditionalCourseDetailTest(TestCase):
    def setUp(self):
        self.teacher = create_teacher()

    def test_show_course_that_belongs_to_teacher(self):
        """Show a course's details that is in the teachers additional courses relationship."""
        course = models.Course.objects.create(name="testcourse")
        self.teacher.additional_courses.add(course)

        self.client.force_login(self.teacher.user)
        response = self.client.get(reverse('teacher:additional_detail', args=(course.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, course.name)

    def test_error_for_course_that_does_not_belong_to_teacher(self):
        """Show an error for a course that is not in the teachers additional courses field."""
        course = models.Course.objects.create(name="testcourse")

        self.client.force_login(self.teacher.user)
        response = self.client.get(reverse('teacher:detail', args=(course.id,)))
        self.assertEqual(response.status_code, 404)


class TeacherCreateCourseTest(TestCase):
    def setUp(self):
        create_teacher()
        self.factory = RequestFactory()

    def test_form_and_formset_in_context_on_get(self):
        """Verify that the context data contains the course form and the weekdays formset on get"""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        self.client.force_login(teacher.user)

        response = self.client.get(reverse('teacher:add'))
        self.assertIn('form', response.context)
        self.assertIn('week_days_formset', response.context)

    def test_render_forms_when_form_invalid_and_form_and_formset_in_context(self):
        """
        Verify that when the form is invalid, the context data contains the course form and the weekdays formset.
        Check for posting missing form data.
        """
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        self.client.force_login(teacher.user)

        response = self.client.post(reverse('teacher:add'), follow=False, data={
            'name': '', 'min_attend_time': '10', 'duration': '20',
            'week_days-TOTAL_FORMS': '0', 'week_days-INITIAL_FORMS': '0',
        })
        self.assertIn('form', response.context)
        self.assertIn('week_days_formset', response.context)

    def test_rerender_forms_on_invalid_formset_form(self):
        """Test add view formset form invalid render to response"""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        self.client.force_login(teacher.user)

        response = self.client.post(reverse('teacher:add'), data={
            'name': 'testcourse', 'min_attend_time': '10', 'duration': '20',
            'week_days-TOTAL_FORMS': '1', 'week_days-INITIAL_FORMS': '0',
            'week_days-0-day': '', 'week_days-0-time': '11:00',
        })
        self.assertIn('form', response.context)
        self.assertIn('week_days_formset', response.context)

    def test_redirect_to_courses_on_successful_course_add(self):
        """Test add view redirect to courses view on successful course add"""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        self.client.force_login(teacher.user)

        response = self.client.post(reverse('teacher:add'), data={
            'name': 'testcourse', 'min_attend_time': '10', 'duration': '20',
            'week_days-TOTAL_FORMS': '0', 'week_days-INITIAL_FORMS': '0',
        })
        self.assertRedirects(response, reverse('teacher:courses'))

    def test_form_valid_without_weekdays(self):
        """Test that form_valid creates course and saves it to the teacher's courses without any weekdays"""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        self.client.force_login(teacher.user)

        request = self.factory.post(reverse('teacher:add'), data={
            'name': 'testcourse_1', 'min_attend_time': '10', 'duration': '20',
            'week_days-TOTAL_FORMS': '0', 'week_days-INITIAL_FORMS': '0',
        })
        request.user = teacher.user

        teachers_view.TeacherCreateCourse.as_view()(request)
        self.assertEqual(models.Course.objects.last().name, 'testcourse_1')
        self.assertIn(models.Course.objects.last(), teacher.courses.all())

    def test_form_valid_with_weekdays(self):
        """Test that form_valid creates course and saves it to the teacher's courses with one weekday"""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        self.client.force_login(teacher.user)

        request = self.factory.post(reverse('teacher:add'), data={
            'name': 'testcourse_2', 'min_attend_time': '10', 'duration': '20',
            'week_days-TOTAL_FORMS': '1', 'week_days-INITIAL_FORMS': '0',
            'week_days-0-day': '0', 'week_days-0-time': '11:00',
        })
        request.user = teacher.user

        teachers_view.TeacherCreateCourse.as_view()(request)
        added_course = models.Course.objects.last()
        added_weekday = models.WeekDay.objects.last()

        self.assertEqual(added_course.name, 'testcourse_2')
        self.assertEqual(added_weekday.day, models.WeekDayChoices.MONDAY)
        self.assertEqual(added_weekday.time, timezone.now().replace(hour=11, minute=0, second=0, microsecond=0).time())
        self.assertIn(added_course, teacher.courses.all())
        self.assertIn(added_weekday, added_course.start_times.all())

    def test_form_valid_with_additional_teacher(self):
        """Test that form_valid creates course and saves it to the teacher's courses with one weekday"""
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        additional_teacher = create_teacher("additional@test.de")
        self.client.force_login(teacher.user)

        request = self.factory.post(reverse('teacher:add'), data={
            'name': 'testcourse_2', 'min_attend_time': '10', 'duration': '20',
            'week_days-TOTAL_FORMS': '0', 'week_days-INITIAL_FORMS': '0',
            'additional_teachers': str(additional_teacher.user.id),
        })
        request.user = teacher.user

        teachers_view.TeacherCreateCourse.as_view()(request)
        added_course = models.Course.objects.last()
        self.assertIn(additional_teacher, added_course.additional_teachers.all())

    def test_invalid_time_in_weekday_gets_ignored(self):
        teacher = models.Teacher.objects.get(user__email=TEACHER_EMAIL)
        self.client.force_login(teacher.user)

        request = self.factory.post(reverse('teacher:add'), data={
            'name': 'testcourse_3', 'min_attend_time': '10', 'duration': '20',
            'week_days-TOTAL_FORMS': '1', 'week_days-INITIAL_FORMS': '0',
            'week_days-0-day': '0', 'week_days-0-time': '',
        })
        request.user = teacher.user
        teachers_view.TeacherCreateCourse.as_view()(request)

        added_course = models.Course.objects.last()
        self.assertEqual(added_course.name, 'testcourse_3')
        self.assertQuerysetEqual(added_course.start_times.all(), [])

class TeacherEditCourseTest(TestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.course = models.Course.objects.create(name='test_course_edit')
        self.factory = RequestFactory()

    def test_form_and_formset_in_context_on_get(self):
        """Verify that the context data contains the course form and the weekdays formset on get"""
        self.client.force_login(self.teacher.user)

        response = self.client.get(reverse('teacher:edit', args=(self.course.id,)))
        self.assertIn('form', response.context)
        self.assertIn('week_days_formset', response.context)

    def test_render_forms_when_form_invalid_and_form_and_formset_in_context(self):
        """
        Verify that when the form is invalid, the context data contains the course form and the weekdays formset.
        Check for posting missing form data.
        """
        self.client.force_login(self.teacher.user)

        response = self.client.post(reverse('teacher:edit', args=(self.course.id,)), follow=False, data={
            'name': '', 'min_attend_time': '10', 'duration': '20',
            'week_days-TOTAL_FORMS': '0', 'week_days-INITIAL_FORMS': '0',
        })
        self.assertIn('form', response.context)
        self.assertIn('week_days_formset', response.context)

    def test_rerender_forms_on_invalid_formset_form(self):
        """Test that an invalid edit-view-formset-form renders to response"""
        self.client.force_login(self.teacher.user)

        response = self.client.post(reverse('teacher:edit', args=(self.course.id,)), data={
            'name': 'testcourse', 'min_attend_time': '10', 'duration': '20',
            'week_days-TOTAL_FORMS': '1', 'week_days-INITIAL_FORMS': '0',
            'week_days-0-day': '', 'week_days-0-time': '11:00',
        })
        self.assertIn('form', response.context)
        self.assertIn('week_days_formset', response.context)

    def test_redirect_to_courses_on_successful_course_add(self):
        """Test edit view redirect to courses view on successful course edit"""
        self.client.force_login(self.teacher.user)

        response = self.client.post(reverse('teacher:edit', args=(self.course.id,)), data={
            'name': 'testcourse', 'min_attend_time': '10', 'duration': '20',
            'week_days-TOTAL_FORMS': '0', 'week_days-INITIAL_FORMS': '0',
        })
        self.assertRedirects(response, reverse('teacher:courses'))

    def test_form_can_change_course_data(self):
        """Test that a valid form can change course data"""
        self.client.force_login(self.teacher.user)
        request = self.factory.post(reverse('teacher:edit', args=(self.course.id,)), data={
            'name': 'testcourse_1', 'min_attend_time': '20', 'duration': '40',
            'week_days-TOTAL_FORMS': '0', 'week_days-INITIAL_FORMS': '0',
        })
        request.user = self.teacher.user
        teachers_view.TeacherEditCourse.as_view()(request, pk=self.course.id)
        course = models.Course.objects.get(pk=self.course.id)

        self.assertEqual(course.name, 'testcourse_1')
        self.assertEqual(course.min_attend_time, 20)
        self.assertEqual(course.duration, 40)

    def test_form_can_delete_weekday(self):
        """Test that a valid form can delete a weekday"""
        self.course.start_times.clear()
        self.course.start_times.add(models.WeekDay.objects.create(
            day=models.WeekDayChoices.MONDAY,
            time=timezone.now().replace(hour=11, minute=0, second=0, microsecond=0).time()
        ))
        data = {
            'name': 'testcourse_1', 'min_attend_time': '20', 'duration': '40',
            'week_days-TOTAL_FORMS': '1', 'week_days-INITIAL_FORMS': '1',
            'week_days-0-id': str(self.course.start_times.first().id), 'week_days-0-DELETE': 'on',
            'week_days-0-day': str(self.course.start_times.first().day),
            'week_days-0-time': self.course.start_times.first().time,
        }
        self.client.force_login(self.teacher.user)
        request = self.factory.post(reverse('teacher:edit', args=(self.course.id,)), data=data)
        request.user = self.teacher.user
        teachers_view.TeacherEditCourse.as_view()(request, pk=self.course.id)

        course = models.Course.objects.get(pk=self.course.id)
        self.assertQuerysetEqual(course.start_times.all(), [])

    def test_form_can_add_weekday(self):
        """Test that a valid form can add a weekday"""
        self.course.start_times.clear()
        data = {
            'name': 'testcourse_1', 'min_attend_time': '20', 'duration': '40',
            'week_days-TOTAL_FORMS': '1', 'week_days-INITIAL_FORMS': '0',
            'week_days-0-id': '', 'week_days-0-DELETE': '',
            'week_days-0-day': '1', 'week_days-0-time': '11:11',
        }
        self.client.force_login(self.teacher.user)
        request = self.factory.post(reverse('teacher:edit', args=(self.course.id,)), data=data)
        request.user = self.teacher.user
        teachers_view.TeacherEditCourse.as_view()(request, pk=self.course.id)

        course = models.Course.objects.get(pk=self.course.id)
        self.assertEqual(course.start_times.first().day, models.WeekDayChoices.TUESDAY)
        self.assertEqual(
            course.start_times.first().time,
            timezone.now().replace(hour=11, minute=11, second=0, microsecond=0).time()
        )

    def test_form_can_edit_weekday(self):
        """Test that a weekday can get edited"""
        self.course.start_times.clear()
        self.course.start_times.add(models.WeekDay.objects.create(
            day=models.WeekDayChoices.MONDAY,
            time=timezone.now().replace(hour=11, minute=0, second=0, microsecond=0).time()
        ))
        data = {
            'name': 'testcourse_1', 'min_attend_time': '20', 'duration': '40',
            'week_days-TOTAL_FORMS': '1', 'week_days-INITIAL_FORMS': '1',
            'week_days-0-id': str(self.course.start_times.first().id), 'week_days-0-DELETE': '',
            'week_days-0-day': '1',
            'week_days-0-time': "11:11",
        }
        self.client.force_login(self.teacher.user)
        request = self.factory.post(reverse('teacher:edit', args=(self.course.id,)), data=data)
        request.user = self.teacher.user
        teachers_view.TeacherEditCourse.as_view()(request, pk=self.course.id)

        course = models.Course.objects.get(pk=self.course.id)
        self.assertEqual(course.start_times.first().day, models.WeekDayChoices.TUESDAY)
        self.assertEqual(
            course.start_times.first().time,
            timezone.now().replace(hour=11, minute=11, second=0, microsecond=0).time()
        )

    def test_form_valid_with_additional_teacher(self):
        """Test that form_valid creates course and saves it to the teacher's courses with one weekday"""
        additional_teacher = create_teacher("additional@test.de")
        self.client.force_login(self.teacher.user)

        request = self.factory.post(reverse('teacher:add'), data={
            'name': 'testcourse_2', 'min_attend_time': '10', 'duration': '20',
            'week_days-TOTAL_FORMS': '0', 'week_days-INITIAL_FORMS': '0',
            'additional_teachers': str(additional_teacher.user.id),
        })
        request.user = self.teacher.user

        teachers_view.TeacherEditCourse.as_view()(request, pk=self.course.id)
        added_course = models.Course.objects.last()
        self.assertIn(additional_teacher, added_course.additional_teachers.all())


class TeacherCourseDeleteTest(TestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.course = create_course(0)
        self.teacher.courses.add(self.course)

    def test_correct_redirect_of_successful_deletion(self):
        self.client.force_login(self.teacher.user)

        response = self.client.post(reverse('teacher:delete', args=(self.course.id,)))
        self.assertRedirects(response, reverse('teacher:courses'))

    def test_let_logged_in_teacher_only_delete_hist_own_courses(self):
        course = create_course(0)
        self.client.force_login(self.teacher.user)

        response = self.client.post(reverse('teacher:delete', args=(course.id,)))
        self.assertEqual(response.status_code, 404)


class TeacherEditTest(TestCase):
    def setUp(self):
        self.teacher = create_teacher()

    def test_correct_redirect_of_successful_edit(self):
        self.client.force_login(self.teacher.user)

        response = self.client.post(reverse('teacher:edit_account', args=(self.teacher.user.id,)), data={
            'email': self.teacher.user.email+'e', 'first_name': 'last', 'last_name': 'first'
        })
        self.assertRedirects(response, reverse('teacher:courses'))

    def test_dont_let_logged_in_teacher_edit_someone_elses_profile(self):
        teacher = create_teacher(custom_email=TEACHER_EMAIL+"2")
        self.client.force_login(self.teacher.user)

        response = self.client.post(reverse('teacher:edit_account', args=(teacher.user.id,)))
        self.assertEqual(response.status_code, 404)


class SettingAccessTokenTest(TestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.course = create_course(0)
        self.teacher.courses.add(self.course)

    def test_course_has_accesstoken(self):
        self.client.force_login(self.teacher.user)
        self.client.get(reverse('teacher:enable_course', args=(self.course.id,)))
        self.course = self.teacher.courses.first()
        self.assertIsNotNone(self.course.access_token)

    def test_token_in_response_context(self):
        self.client.force_login(self.teacher.user)
        response = self.client.get(reverse('teacher:enable_course', args=(self.course.id,)))
        self.course = self.teacher.courses.first()
        self.assertContains(response, self.course.access_token.token)

    def test_teacher_that_does_not_own_course_cant_set_token(self):
        course = create_course(0)
        self.client.force_login(self.teacher.user)
        response = self.client.get(reverse('teacher:enable_course', args=(course.id,)))
        self.assertEqual(response.status_code, 404)


class GetCoursesStatesTest(TestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.course = create_course(0)

    def test_empty_dict_when_teacher_has_no_courses(self):
        self.client.force_login(self.teacher.user)
        response = self.client.get(reverse('teacher:courses_status'))
        self.assertJSONEqual(str(response.content, encoding='utf8'), {})

    @mock.patch('django.utils.timezone.now', return_value=NOW_FOR_TESTING)
    def test_course_not_ongoing(self, *args):
        self.course.start_times.create(
            day=models.WeekDayChoices.FRIDAY,
            time=timezone.now().replace(hour=9, minute=0, second=0, microsecond=0).time()
        )
        self.teacher.courses.add(self.course)
        self.teacher.refresh_from_db()
        self.client.force_login(self.teacher.user)
        response = self.client.get(reverse('teacher:courses_status'))
        self.assertJSONEqual(str(response.content, encoding='utf8'), {str(self.course.id): False})

    @mock.patch('django.utils.timezone.now', return_value=NOW_FOR_TESTING)
    def test_course_ongoing(self, *args):
        self.course.start_times.create(
            day=models.WeekDayChoices.MONDAY,
            time=timezone.now().time()
        )
        self.teacher.courses.add(self.course)
        self.teacher.refresh_from_db()
        self.client.force_login(self.teacher.user)
        response = self.client.get(reverse('teacher:courses_status'))
        self.assertJSONEqual(str(response.content, encoding='utf8'), {str(self.course.id): True})
