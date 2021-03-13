import secrets
from uuid import uuid4

from django.utils import timezone
from django.db import models
from django.urls import reverse


class WeekDayChoices(models.IntegerChoices):
    MONDAY = 0, 'MON'
    TUESDAY = 1, 'TUE'
    WEDNESDAY = 2, 'WED'
    THURSDAY = 3, 'THU'
    FRIDAY = 4, 'FRI'
    SATURDAY = 5, 'SAT'
    SUNDAY = 6, 'SUN'


class WeekDay(models.Model):
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

    def get_this_weeks_date(self):
        now = timezone.localtime(timezone.localtime().replace(
            hour=self.time.hour,
            minute=self.time.minute,
            second=self.time.second,
            microsecond=0
        ), timezone.utc)
        return now + timezone.timedelta(days=-now.weekday()+self.day)

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
            self.created = timezone.now()
            self.token = secrets.token_urlsafe(10)
        return super().save(*args, **kwargs)

    def is_token_valid(self, given_token):
        if self.token == given_token:
            return True
        return False

    def is_token_expired(self):
        expiration_time = self.created + timezone.timedelta(seconds=self.valid_time*60)
        if timezone.now() < expiration_time:
            return False
        return True

    def __str__(self):
        return f"created: {self.created}, valid for {self.valid_time}"


class Course(models.Model):
    name = models.CharField("course name", max_length=200)
    uuid = models.UUIDField("course identifier", primary_key=False, unique=True, default=uuid4, editable=False)
    min_attend_time = models.IntegerField("minimum time present to count as attended in minutes", default=45)
    duration = models.IntegerField("course duration in minutes", default=90)
    ongoing = models.BooleanField(default=False)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='courses', null=True)

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

    def is_ongoing(self):
        if self.ongoing:
            return True

        for day in self.start_times.all():
            max_duration_day = day.get_this_weeks_date() + timezone.timedelta(minutes=self.duration)
            if day.get_this_weeks_date() <= timezone.now() < max_duration_day:
                return True
        return False

    def get_next_date(self):
        """Get the next date the course is taking place.
        If there are no dates for this course, return None.
        """
        next_dates = []
        for weekday in self.start_times.all():
            weekday_endtime = weekday.get_this_weeks_date() + timezone.timedelta(minutes=self.duration)
            if weekday_endtime > timezone.now():
                next_dates.append(weekday_endtime)
        if next_dates:
            return min(next_dates) - timezone.timedelta(minutes=self.duration)
        return None

    @property
    def sorted_start_times_set(self):
        return sorted(list(self.start_times.all()), key=lambda wd: wd.get_this_weeks_date())

    def __str__(self):
        return (
            f"name: {self.name}, "
            f"min_attend_time: {self.min_attend_time}, "
            f"duration: {self.duration}"
        )
