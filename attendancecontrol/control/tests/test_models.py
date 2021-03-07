import datetime

import mock
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .test_view_students import create_student
from .test_view_teachers import create_teacher
from ..models import User, WeekDay, WeekDayChoices, AccessToken, Course

# Make now() a constant
NOW_FOR_TESTING = timezone.make_aware(
    timezone.datetime(2021, 3, 1, 10, 0, 0, 0),  # 1.3.2021 was a monday
    timezone.utc
)
TIME_FOR_TESTING = timezone.make_aware(
    timezone.datetime(2021, 3, 1, 9, 55, 0, 0),  # 1.3.2021 was a monday
    timezone.utc
).time()


def mocked_now():
    """function that replaces django.utils.timezone.now()"""
    return NOW_FOR_TESTING


class UserManagerTest(TestCase):
    def test_user_manager_raises_valueerror_on_missing_email(self):
        self.assertRaises(ValueError, User.objects.create_user, email='', password='')

    def test_successful_user_creation(self):
        User.objects.create_user(email='asd<html>@test.de', password="testpassword123")
        last_user = User.objects.last()
        self.assertIs(last_user.check_password("testpassword123"), True)

    def test_create_successful_superuser(self):
        User.objects.create_superuser(email='test@test.de', password='123456password')
        last_user = User.objects.last()
        self.assertIs(last_user.is_staff, True)
        self.assertIs(last_user.is_superuser, True)
        self.assertIs(last_user.is_active, True)

    def test_create_superuser_without_is_staff_raises_valueerror(self):
        self.assertRaises(
            ValueError,
            User.objects.create_superuser,
            email='test@test.de', password='123456password', is_staff=False
        )

    def test_create_superuser_without_is_superuser_raises_valueerror(self):
        self.assertRaises(
            ValueError,
            User.objects.create_superuser,
            email='test@test.de', password='123456password', is_superuser=False
        )


class UserModelTest(TestCase):
    def test_user_model_str(self):
        user = User.objects.create_user(email='test@test.de', password='testpassword')
        self.assertEqual(str(user), 'test@test.de')


@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
class WeekDayModelTests(TestCase):
    def setUp(self) -> None:
        self.weekday = WeekDay.objects.create(day=WeekDayChoices.MONDAY, time=TIME_FOR_TESTING)

    def test_weekday_model_str_function(self, *args):
        self.assertEqual(
            str(self.weekday),
            f"day: {WeekDayChoices(self.weekday.day).label}, time: {self.weekday.time}")

    def test_get_this_weeks_date_is_acutal_weeks_date(self, *args):
        """get_this_weeks_date() equals actual weeks date"""
        weekday = WeekDay.objects.get(day=WeekDayChoices.MONDAY, time=TIME_FOR_TESTING)
        actual_weekday = NOW_FOR_TESTING.replace(hour=TIME_FOR_TESTING.hour, minute=TIME_FOR_TESTING.minute)
        self.assertEqual(weekday.get_this_weeks_date(), actual_weekday)

    def test_get_this_weeks_date_is_not_acutal_weeks_date(self, *args):
        """get_this_weeks_date() does not equal wrong weeks date (off by 5mins)"""
        weekday = WeekDay.objects.get(day=WeekDayChoices.MONDAY, time=TIME_FOR_TESTING)
        self.assertNotEqual(weekday.get_this_weeks_date(), NOW_FOR_TESTING)

    def test_get_this_weeks_date_correct_day_of_the_week(self, *args):
        """
        test if get_this_weeks_date() returns correct day of the week.
        startdate is 1st of march 2021, a monday.
        Go through days in weekdaychoices and increment startdate by one day.
        """
        start_date = NOW_FOR_TESTING
        for day in WeekDayChoices.values:
            with mock.patch('django.utils.timezone.now', return_value=start_date):
                weekday = WeekDay.objects.create(day=WeekDayChoices(day), time=start_date.time())
                self.assertEqual(weekday.get_this_weeks_date(), start_date)
                start_date = start_date + timezone.timedelta(hours=24)


@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
class AccessTokenModelTests(TestCase):
    def setUp(self, *args):
        AccessToken.objects.create(valid_time=10)

    def test_accesstoken_model_str_function(self, *args):
        token = AccessToken.objects.last()
        self.assertEqual(str(token), f"created: {token.created}, valid for {token.valid_time}")

    def test_is_token_valid_with_valid_token(self, *args):
        """is_token_valid() returns True when called with its own created token"""
        token = AccessToken.objects.last()
        self.assertIs(token.is_token_valid(token.token), True)

    def test_is_token_expired_with_valid_token(self, *args):
        """is_token_expired() returns False when inside the created+valid_time time interval"""
        token = AccessToken.objects.last()
        self.assertIs(token.is_token_expired(), False)


@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
class CourseModelTests(TestCase):
    def setUp(self, *args):
        Course.objects.create(name="TestCourse", duration=10, min_attend_time=5, ongoing=True)
        WeekDay.objects.create(day=WeekDayChoices.MONDAY, time=TIME_FOR_TESTING)

    def test_course_model_str_function(self, *args):
        course = Course.objects.last()
        self.assertEqual(
            str(course),
            f"name: {course.name}, min_attend_time: {course.min_attend_time}, duration: {course.duration}"
        )

    def test_is_ongoing_with_ongoing_flag_set(self, *arg):
        """is_ongoing() returns True for courses which ongoing flag is set to True"""
        course = Course.objects.get(name="TestCourse")
        course.ongoing = True
        self.assertIs(course.is_ongoing(), True)

    def test_is_not_ongoing_with_ongoing_flag_not_set(self, *arg):
        """is_ongoing() returns False for courses which ongoing flag is set to False"""
        course = Course.objects.get(name="TestCourse")
        course.ongoing = False
        self.assertIs(course.is_ongoing(), False)

    def test_is_ongoing_with_current_time_in_start_time_plus_duration_interval(self, *arg):
        """
        is_ongoing() returns True for courses which have a start_time interval inside the current time.
        start_time intervals are:
            [this weeks start date and time:this weeks start date and time + courses duration]
        """
        course = Course.objects.get(name="TestCourse")
        course.ongoing = False
        weekday, _ = WeekDay.objects.get_or_create(day=WeekDayChoices.MONDAY, time=TIME_FOR_TESTING)
        course.start_times.add(weekday)
        self.assertIs(course.is_ongoing(), True)
        course.start_times.remove(weekday)

    def test_is_not_ongoing_with_current_time_not_in_start_time_plus_duration_interval(self, *arg):
        """
        is_ongoing() returns False for courses which have a start_time interval outside of the current time.
        start_time intervals are:
            [this weeks start date and time:this weeks start date and time + courses duration]
        Test this for all days of the week.
        """
        course = Course.objects.get(name="TestCourse")
        course.ongoing = False

        for day in WeekDayChoices.values:
            daytime = datetime.datetime.combine(
                datetime.date.today(),
                TIME_FOR_TESTING
            ) + datetime.timedelta(minutes=20)
            weekday, _ = WeekDay.objects.get_or_create(
                day=WeekDayChoices(day), time=daytime.time()
            )
            course.start_times.add(weekday)
            self.assertIs(course.is_ongoing(), False)
            course.start_times.remove(weekday)

    def test_course_get_absolute_student_register_url_without_access_token(self, *args):
        course = Course.objects.create(name='testcourseforurl')
        self.assertEqual(
            course.get_absolute_student_register_url(),
            reverse('student:register_course', args=[str(course.id), 'INVALID_TOKEN'])
        )

    def test_course_get_absolute_student_register_url_with_access_token(self, *args):
        course = Course.objects.create(name='testcourseforurl')
        token = AccessToken.objects.create()
        course.access_token = token
        course.save()
        self.assertEqual(
            course.get_absolute_student_register_url(),
            reverse('student:register_course', args=[str(course.id), token.token])
        )


class StudentModelTests(TestCase):
    def test_student_model_str_function(self):
        student = create_student()
        self.assertEqual(str(student), f"user: {student.user}, stud.nr {student.student_nr}, mac: {student.mac}")


class TeacherModelTests(TestCase):
    def test_teacher_model_str_function(self):
        teacher = create_teacher()
        self.assertEqual(str(teacher), f"{teacher.user}")
