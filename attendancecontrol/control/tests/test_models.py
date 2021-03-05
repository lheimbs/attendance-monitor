import mock
import datetime

from django.test import TestCase
from django.utils import timezone
from mock.mock import _set_return_value

from ..models import WeekDay, WeekDayChoices, AccessToken, Course

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


def a_func():
    """shows that the mocking is in effect even outside of the Test scope"""
    return timezone.now()


@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
class CourseModelTests(TestCase):
    def setUp(self, *args):
        Course.objects.create(name="TestCourse", duration=10, min_attend_time=5, ongoing=True)
        WeekDay.objects.create(day=WeekDayChoices.MONDAY, time=TIME_FOR_TESTING)

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


@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
class AccessTokenModelTests(TestCase):
    def setUp(self, *args):
        AccessToken.objects.create(valid_time=10)

    def test_is_token_valid_with_valid_token(self, *args):
        """is_token_valid() returns True when called with its own created token"""
        token = AccessToken.objects.last()
        self.assertIs(token.is_token_valid(token.token), True)

    def test_is_token_expired_with_valid_token(self, *args):
        """is_token_expired() returns False when inside the created+valid_time time interval"""
        token = AccessToken.objects.last()
        self.assertIs(token.is_token_expired(), False)

@mock.patch('django.utils.timezone.now', side_effect=mocked_now)
class WeekDayModelTests(TestCase):
    def setUp(self) -> None:
        WeekDay.objects.create(day=WeekDayChoices.MONDAY, time=TIME_FOR_TESTING)

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
