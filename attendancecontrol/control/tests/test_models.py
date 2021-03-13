import datetime
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .test_view_students import create_student
from .test_view_teachers import create_teacher

from ..models import users as user_models
from ..models import courses as course_models

# Make now() a constant
NOW_FOR_TESTING = timezone.make_aware(
    timezone.datetime(2021, 3, 1, 10, 0, 0, 0),  # 1.3.2021 was a monday
    timezone.get_current_timezone()
)
TIME_FOR_TESTING = timezone.make_aware(
    timezone.datetime(2021, 3, 1, 9, 55, 0, 0),  # 1.3.2021 was a monday
    timezone.get_current_timezone()
).time()


def mocked_now():
    """function that replaces django.utils.timezone.now()"""
    return NOW_FOR_TESTING


class UserManagerTest(TestCase):
    def test_user_manager_raises_valueerror_on_missing_email(self):
        self.assertRaises(ValueError, user_models.User.objects.create_user, email='', password='')

    def test_successful_user_creation(self):
        user_models.User.objects.create_user(email='asd<html>@test.de', password="testpassword123")
        last_user = user_models.User.objects.last()
        self.assertIs(last_user.check_password("testpassword123"), True)

    def test_create_successful_superuser(self):
        user_models.User.objects.create_superuser(email='test@test.de', password='123456password')
        last_user = user_models.User.objects.last()
        self.assertIs(last_user.is_staff, True)
        self.assertIs(last_user.is_superuser, True)
        self.assertIs(last_user.is_active, True)

    def test_create_superuser_without_is_staff_raises_valueerror(self):
        self.assertRaises(
            ValueError,
            user_models.User.objects.create_superuser,
            email='test@test.de', password='123456password', is_staff=False
        )

    def test_create_superuser_without_is_superuser_raises_valueerror(self):
        self.assertRaises(
            ValueError,
            user_models.User.objects.create_superuser,
            email='test@test.de', password='123456password', is_superuser=False
        )


class UserModelTest(TestCase):
    def test_user_model_str(self):
        user = user_models.User.objects.create_user(email='test@test.de', password='testpassword')
        self.assertEqual(str(user), 'test@test.de')


@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
class WeekDayModelTests(TestCase):
    def setUp(self) -> None:
        self.weekday = course_models.WeekDay.objects.create(
            day=course_models.WeekDayChoices.MONDAY,
            time=TIME_FOR_TESTING
        )

    def test_weekday_model_str_function(self, *args):
        self.assertEqual(
            str(self.weekday),
            f"day: {course_models.WeekDayChoices(self.weekday.day).label}, time: {self.weekday.time}")

    def test_get_this_weeks_date_is_acutal_weeks_date(self, *args):
        """get_this_weeks_date() equals actual weeks date"""
        weekday = course_models.WeekDay.objects.get(day=course_models.WeekDayChoices.MONDAY, time=TIME_FOR_TESTING)
        actual_weekday = NOW_FOR_TESTING.replace(hour=TIME_FOR_TESTING.hour, minute=TIME_FOR_TESTING.minute)
        self.assertEqual(weekday.get_this_weeks_date(), actual_weekday)

    def test_get_this_weeks_date_is_not_acutal_weeks_date(self, *args):
        """get_this_weeks_date() does not equal wrong weeks date (off by 5mins)"""
        weekday = course_models.WeekDay.objects.get(day=course_models.WeekDayChoices.MONDAY, time=TIME_FOR_TESTING)
        self.assertNotEqual(weekday.get_this_weeks_date(), NOW_FOR_TESTING)

    def test_get_this_weeks_date_correct_day_of_the_week(self, *args):
        """
        test if get_this_weeks_date() returns correct day of the week.
        startdate is 1st of march 2021, a monday.
        Go through days in weekdaychoices and increment startdate by one day.
        """
        start_date = NOW_FOR_TESTING
        for day in course_models.WeekDayChoices.values:
            with mock.patch('django.utils.timezone.now', return_value=start_date):
                weekday = course_models.WeekDay.objects.create(
                    day=course_models.WeekDayChoices(day), time=start_date.time()
                )
                self.assertEqual(weekday.get_this_weeks_date(), start_date)
                start_date = start_date + timezone.timedelta(hours=24)


@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
class AccessTokenModelTests(TestCase):
    def setUp(self, *args):
        course_models.AccessToken.objects.create(valid_time=10)

    def test_accesstoken_model_str_function(self, *args):
        token = course_models.AccessToken.objects.last()
        self.assertEqual(str(token), f"created: {token.created}, valid for {token.valid_time}")

    def test_is_token_valid_with_valid_token(self, *args):
        """is_token_valid() returns True when called with its own created token"""
        token = course_models.AccessToken.objects.last()
        self.assertIs(token.is_token_valid(token.token), True)

    def test_is_token_expired_with_valid_token(self, *args):
        """is_token_expired() returns False when inside the created+valid_time time interval"""
        token = course_models.AccessToken.objects.last()
        self.assertIs(token.is_token_expired(), False)


@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
class CourseModelTests(TestCase):
    def setUp(self, *args):
        self.course = course_models.Course.objects.create(
            name="Testcourse_models.Course", duration=10, min_attend_time=5, ongoing=True
        )
        self.wd = course_models.WeekDay.objects.create(
            day=course_models.WeekDayChoices.MONDAY, time=TIME_FOR_TESTING
        )

    def test_course_model_str_function(self, *args):
        course = course_models.Course.objects.last()
        self.assertEqual(
            str(course),
            f"name: {course.name}, min_attend_time: {course.min_attend_time}, duration: {course.duration}"
        )

    def test_is_ongoing_with_ongoing_flag_set(self, *arg):
        """is_ongoing() returns True for courses which ongoing flag is set to True"""
        course = course_models.Course.objects.get(name="Testcourse_models.Course")
        course.ongoing = True
        self.assertIs(course.is_ongoing(), True)

    def test_is_not_ongoing_with_ongoing_flag_not_set(self, *arg):
        """is_ongoing() returns False for courses which ongoing flag is set to False"""
        course = course_models.Course.objects.get(name="Testcourse_models.Course")
        course.ongoing = False
        self.assertIs(course.is_ongoing(), False)

    def test_is_ongoing_with_current_time_in_start_time_plus_duration_interval(self, *arg):
        """
        is_ongoing() returns True for courses which have a start_time interval inside the current time.
        start_time intervals are:
            [this weeks start date and time:this weeks start date and time + courses duration]
        """
        course = course_models.Course.objects.get(name="Testcourse_models.Course")
        course.ongoing = False
        weekday, _ = course_models.WeekDay.objects.get_or_create(
            day=course_models.WeekDayChoices.MONDAY, time=TIME_FOR_TESTING
        )
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
        course = course_models.Course.objects.get(name="Testcourse_models.Course")
        course.ongoing = False

        for day in course_models.WeekDayChoices.values:
            daytime = datetime.datetime.combine(
                datetime.date.today(),
                TIME_FOR_TESTING
            ) + datetime.timedelta(minutes=20)
            weekday, _ = course_models.WeekDay.objects.get_or_create(
                day=course_models.WeekDayChoices(day), time=daytime.time()
            )
            course.start_times.add(weekday)
            self.assertIs(course.is_ongoing(), False)
            course.start_times.remove(weekday)

    def test_course_get_absolute_student_register_url_without_access_token(self, *args):
        course = course_models.Course.objects.create(name='testcourseforurl')
        self.assertEqual(
            course.get_absolute_student_register_url(),
            reverse('student:register_course', args=[str(course.id), 'INVALID_TOKEN'])
        )

    def test_course_get_absolute_student_register_url_with_access_token(self, *args):
        course = course_models.Course.objects.create(name='testcourseforurl')
        token = course_models.AccessToken.objects.create()
        course.access_token = token
        course.save()
        self.assertEqual(
            course.get_absolute_student_register_url(),
            reverse('student:register_course', args=[str(course.id), token.token])
        )

    def test_course_get_absolute_additional_teacher_url(self, *args):
        course = course_models.Course.objects.create(name='testcourseforurl')
        teacher = create_teacher()
        teacher.additional_courses.add(course)
        self.assertEqual(
            course.get_absolute_additional_teacher_url(),
            reverse('teacher:additional_detail', args=[str(course.id)])
        )

    def test_course_get_next_date_correct_date_with_one_date(self, *args):
        self.course.start_times.clear()
        self.course.start_times.add(self.wd)
        next_date = self.course.get_next_date()
        self.assertEqual(next_date, self.wd.get_this_weeks_date())

    def test_course_get_next_date_none_for_this_week_alreay_happened(self, *args):
        self.course.start_times.clear()
        wd_2 = course_models.WeekDay.objects.create(
            day=course_models.WeekDayChoices.MONDAY,
            time=TIME_FOR_TESTING.replace(hour=2)
        )
        self.course.start_times.add(wd_2)
        next_date = self.course.get_next_date()
        self.assertEqual(next_date, None)

    def test_course_get_sorted_start_times_set(self, *args):
        self.course.start_times.clear()
        wd_2 = course_models.WeekDay.objects.create(
            day=course_models.WeekDayChoices.MONDAY,
            time=TIME_FOR_TESTING.replace(hour=2)
        )
        self.course.start_times.add(self.wd, wd_2)
        self.assertListEqual(self.course.sorted_start_times_set, [wd_2, self.wd])

class StudentModelTests(TestCase):
    def test_student_model_str_function(self):
        student = create_student()
        self.assertEqual(str(student), f"user: {student.user}, stud.nr {student.student_nr}, mac: {student.mac}")


class TeacherModelTests(TestCase):
    def setUp(self):
        self.teacher = create_teacher()

    def test_teacher_model_str_function(self):
        self.assertEqual(str(self.teacher), f"{self.teacher.user}")

    def test_teacher_full_name_property(self):
        self.assertEqual(self.teacher.get_full_name, f"{self.teacher.user.first_name} {self.teacher.user.last_name}")
