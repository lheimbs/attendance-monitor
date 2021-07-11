import secrets
import logging
from typing import Tuple, Union
from uuid import uuid4

from django.utils import timezone
from django.db import models
from django.urls import reverse

from .base import BaseUpdatingModel

logger = logging.getLogger('control')

class WeekDayChoices(models.IntegerChoices):
    MONDAY = 0, 'MON'
    TUESDAY = 1, 'TUE'
    WEDNESDAY = 2, 'WED'
    THURSDAY = 3, 'THU'
    FRIDAY = 4, 'FRI'
    SATURDAY = 5, 'SAT'
    SUNDAY = 6, 'SUN'


class WeekDay(BaseUpdatingModel):
    day = models.IntegerField(
        "course day",
        choices=WeekDayChoices.choices,
        default=WeekDayChoices.MONDAY,
    )
    time = models.TimeField("starting time of course")
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='start_times', null=True)

    def __str__(self):
        return "day: {}, time: {}".format(
            WeekDayChoices(self.day).label, self.time
        )

    def get_this_weeks_date(self, reference_date: timezone.datetime = None):
        one_week_delta = timezone.timedelta(days=7)
        if reference_date:
            now = reference_date
        else:
            now = timezone.localtime()
        localtime = timezone.get_current_timezone().localize(
            timezone.datetime.combine(timezone.localtime().date(), self.time)
        ).timetz()

        now = now.combine(now.date(), localtime)
        now = now.replace(
            # hour=self.time.hour,
            # minute=self.time.minute,
            # second=self.time.second,
            microsecond=0
        )
        now = now + timezone.timedelta(days=-now.weekday()+self.day)
        if reference_date and now < reference_date:
            now = now + one_week_delta
        # logger.debug(f"{self!r}: get_this_weeks_date({reference_date}) -> {now}")
        return now

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_day_valid",
                check=models.Q(day__in=WeekDayChoices.values),
            )
        ]


class AccessToken(models.Model):
    token = models.CharField("Access Token", max_length=20, editable=False)
    created = models.DateTimeField("Time the token has been generated", editable=False)

    # added for future functionality where valid time is configurable
    valid_time = models.IntegerField("Minutes the token is valid for", default=90)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.localtime()
            self.token = secrets.token_urlsafe(10)
        return super().save(*args, **kwargs)

    def is_token_valid(self, given_token):
        if self.token == given_token:
            return True
        return False

    def is_token_expired(self):
        expiration_time = self.created + timezone.timedelta(minutes=self.valid_time)
        if timezone.localtime() < expiration_time:
            return False
        return True

    def __str__(self):
        return f"created={self.created}, valid_time={self.valid_time}"


class Course(BaseUpdatingModel):
    name = models.CharField("course name", max_length=200)
    uuid = models.UUIDField("course identifier", primary_key=False, unique=True, default=uuid4, editable=False)
    min_attend_time = models.IntegerField("minimum time present to count as attended in minutes", default=45)
    duration = models.IntegerField("course duration in minutes", default=90)
    ongoing = models.BooleanField(default=False)
    start_date = models.DateTimeField("start date of the course", blank=True, null=True)
    end_date = models.DateTimeField("end date of the course", blank=True, null=True)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='courses', null=True)

    token_valid_time = models.IntegerField("time until the registration token expires", default=90)
    access_token = models.OneToOneField(AccessToken, on_delete=models.CASCADE, null=True, blank=True)

    def get_absolute_student_url(self):
        return reverse('student:detail', args=[str(self.id)])

    def get_absolute_student_leave_url(self):
        return reverse('student:leave_course', args=[str(self.id)])

    def get_absolute_student_register_url(self):
        if hasattr(self, 'access_token') and self.access_token:
            token = self.access_token.token
        else:
            token = "INVALID_TOKEN"
        return reverse('student:register_course', args=[str(self.id), token])

    def get_absolute_teacher_url(self):
        return reverse('teacher:detail', args=[str(self.id)])

    def get_absolute_additional_teacher_url(self):
        return reverse('teacher:additional_detail', args=[str(self.id)])

    def get_absolute_teacher_delete_url(self):
        return reverse('teacher:delete', args=[str(self.id)])

    def get_absolute_teacher_edit_url(self):
        return reverse('teacher:edit', args=[str(self.id)])

    def is_ongoing(self) -> Tuple[WeekDay, timezone.datetime, int]:
        # if self.ongoing:
        #     return True
        ongoing = tuple()
        for day in self.start_times.all():
            start_date = day.get_this_weeks_date()
            max_duration_day = start_date + timezone.timedelta(minutes=self.duration)
            if start_date <= timezone.localtime() < max_duration_day:
                ongoing = (day, start_date, max_duration_day)
        # logger.debug(f"{self!r}: is_ongoing() -> {ongoing}")
        return ongoing

    def get_next_date(self, time: timezone.datetime = None) -> Union[None, timezone.datetime]:
        """Get the next date the course is taking place.

        If there are no dates for this course, return None.
        """
        if not time:
            time = timezone.localtime()

        next_dates = []
        course_duration = timezone.timedelta(minutes=self.duration)
        for weekday in self.start_times.all():
            weekday_endtime = weekday.get_this_weeks_date(time) + course_duration
            if weekday_endtime > time:
                next_dates.append(weekday_endtime)
        # logger.debug(f"{self!r}: get_next_date() -> {next_dates}")
        if next_dates:
            return min(next_dates) - course_duration
        return None

    def days_since_start(self, day: WeekDay, start_date: timezone.datetime = None) -> list[timezone.datetime]:
        days = []
        next_week = timezone.timedelta(days=7)
        end_date = self.end_date if self.end_date < timezone.localtime() else timezone.localtime()

        if not start_date:
            start_date = self.start_date

        if day.day < self.get_next_date(self.start_date).weekday():
            days.append(None)

        while start_date < end_date:
            weeks_date = day.get_this_weeks_date(start_date)
            if weeks_date < end_date:
                days.append(weeks_date)
            start_date += next_week
        return days

    @property
    def sorted_start_times_set(self) -> list[WeekDay]:
        return sorted(list(self.start_times.all()), key=lambda wd: wd.get_this_weeks_date())

    def __str__(self) -> str:
        return (
            f"name={self.name}, "
            f"min_attend_time={self.min_attend_time}, "
            f"duration={self.duration}"
        )


class AttendanceRecord(BaseUpdatingModel):
    arrival = models.DateTimeField()
    departure = models.DateTimeField(null=True, blank=True)
    time_present = models.FloatField(default=0.0, db_column='attended')
    weekday = models.ForeignKey(WeekDay, on_delete=models.SET_NULL, null=True)

    student_course = models.ForeignKey('CourseStudentAttendance',
                                       on_delete=models.SET_NULL,
                                       blank=True,
                                       null=True,
                                       related_name='attendance_dates')

    def __str__(self):
        return (
            f'arrival={self.arrival}, '
            f'departure={self.departure}, '
            f'time_present={self.time_present}, '
            f'weekday=WeekDay({self.weekday}), '
            f'course=<Course({self.student_course.course}), '
            f'student=<Student({self.student_course.student})'
        )


class CourseStudentAttendance(BaseUpdatingModel):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    # attendance_dates comes from AttendanceRecors FK

    def get_attendance(self, time: timezone.datetime = None, minutes: bool = False):
        if not time:
            time = self.course.start_date

        stud_days = []
        num_days = 0
        for i, day in enumerate(self.course.sorted_start_times_set):
            stud_attends = []
            for start in self.course.days_since_start(day, time):
                if not start:
                    stud_attends.append(None)
                    continue
                time_attended = self.get_time_present(start)
                if minutes:
                    time_attended /= 60
                min_attend_time = self.course.min_attend_time if minutes else self.course.min_attend_time * 60
                status = time_attended / min_attend_time
                if status >= 1:
                    status = 'success'
                elif 0.5 >= status > 1:
                    status = 'warning'
                else:
                    status = 'danger'
                stud_attends.append((start, time_attended, status))
            if i == 0:
                num_days = len(stud_attends)
            else:
                while len(stud_attends) < num_days:
                    stud_attends.append(None)
            stud_days.append({
                'name': day.get_day_display(),
                'time': day.time.strftime('%H:%M'),
                'attendances': stud_attends
            })
        return stud_days

    def get_current_attendance(self, minutes: bool = False) -> float:
        if not self.course.is_ongoing():
            return 0.0

        next_date = self.course.get_next_date(timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0))
        if not next_date:
            return 0.0

        time_attended = self.get_time_present(next_date)
        if minutes:
            time_attended /= 60
        return time_attended

    def get_time_present(self, reference_date: timezone.datetime) -> float:
        end = reference_date + timezone.timedelta(minutes=self.course.duration)
        min_arrival = reference_date.replace(hour=6, minute=0, second=0, microsecond=0)
        max_arrival = end - timezone.timedelta(minutes=self.course.min_attend_time)
        time_attended = 0
        recorded_arrivals = self.attendance_dates.filter(arrival__range=[min_arrival, max_arrival])
        for ar in recorded_arrivals:
            ar_start = reference_date if reference_date > ar.arrival else ar.arrival
            departure = ar.departure if ar.departure else timezone.localtime()
            ar_end = end if end < departure else departure
            time_attended += (ar_end - ar_start).total_seconds()
        return time_attended

    def __str__(self):
        return (
            f'student={repr(self.student) if self.student else None}, '
            f'course={repr(self.course) if self.course else None}, '
            f'attendance_dates={self.attendance_dates.all()}'
        )
