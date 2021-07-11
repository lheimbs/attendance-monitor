
import uuid
import logging

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ObjectDoesNotExist

from macaddress.fields import MACAddressField
from macaddress import default_dialect
from rest_framework.authtoken.models import Token
from django_fsm import FSMField, transition

from .base import BaseUpdatingModel

logger = logging.getLogger('control')

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

    # username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class Student(BaseUpdatingModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    wifi_info = models.OneToOneField('WifiInfo', on_delete=models.SET_NULL, null=True, blank=True)
    student_nr = models.IntegerField(_("matrikel nr"))
    courses = models.ManyToManyField('Course', through='CourseStudentAttendance')

    def __str__(self):
        return f"user: {self.user}, stud.nr {self.student_nr}, mac: {self.wifi_info.mac if self.wifi_info else ''}"


class ArrivalThreshholdExceededError(Exception):
    """Raised when a probes arrival time has exceeded the arrival threshold."""
    pass


class DepartureThreshholdNotReachedError(Exception):
    """Raised when a probes departure time has not exceeded the departure threshold."""
    pass


class WithdrawalThresholdNotReachedError(Exception):
    """Raised when a probes withdrawal time has not exceeded the withdrawal threshold."""
    pass


class State:
    INITIAL = 'initial stage'
    POTENTIAL_ARRIVAL = 'potential arrival'
    ARRIVAL = 'arrive confirmation'
    POTENTIAL_DEPARTURE = 'potential departure'
    DEPARTURE = 'departure confirmation'

    CHOICES = (
        (INITIAL, INITIAL.title()),
        (POTENTIAL_ARRIVAL, POTENTIAL_ARRIVAL.title()),
        (ARRIVAL, ARRIVAL.title()),
        (POTENTIAL_DEPARTURE, POTENTIAL_DEPARTURE.title()),
        (DEPARTURE, DEPARTURE.title())
    )
    INITIAL_STATE = INITIAL


class WifiInfo(BaseUpdatingModel):
    mac = MACAddressField(null=True, unique=True, integer=False)
    burst_interval = models.FloatField(default=60*60, db_column='mac_burst_interval')   # 30 minutes default
    burst_variance = models.FloatField(default=15*60, db_column='mac_burst_variance')   # 15 minutes default
    burst_count = models.PositiveIntegerField(default=0, db_column='mac_burst_count')
    burst_updated = models.DateTimeField(blank=True, null=True, db_column='mac_burst_updated')

    ARRIVAL_THRESHOLD = 60   # sixty seconds constant to differentiate probe bursts
    latest_recieved_probe_time = models.DateTimeField(blank=True, null=True)
    state = FSMField(max_length=50,
                     choices=State.CHOICES,
                     default=State.INITIAL_STATE,
                     protected=True)

    @transition(field=state, source=State.INITIAL, target=State.POTENTIAL_ARRIVAL)
    def initial_probe_detected(self, probe):
        """A probe request from this MAC address source is recieved.

        Advance to state 1 (potential arrival)."""
        self.latest_recieved_probe_time = probe.time

    @transition(field=state, source=State.POTENTIAL_ARRIVAL, target=State.ARRIVAL)
    def arrival_threshold(self, probe):
        """A probe request from this MAC address source is detected again.

        Advance to ARRIVAL state if the probe came inside the arrival threshold time."""
        arrival_threshold = self.latest_recieved_probe_time + timezone.timedelta(seconds=self.ARRIVAL_THRESHOLD)
        if probe.time > arrival_threshold:
            raise ArrivalThreshholdExceededError

        self.latest_recieved_probe_time = probe.time
        add_arrival(self, probe.time)

    @transition(field=state, source=State.POTENTIAL_ARRIVAL, target=State.INITIAL)
    def arrival_threshold_exceeded(self):
        """The ARRIVAL_THRESHOLD was exceeded. Return to initial state of SM."""
        pass

    @transition(field=state, source=State.ARRIVAL, target=State.POTENTIAL_DEPARTURE)
    def without_probes_recently(self, probe=None):
        """Check if there were any probes recieved inside the departure threshold."""
        withdrawal_threshold = self.latest_recieved_probe_time + timezone.timedelta(
            seconds=self.burst_interval)
        if probe is None:
            now = timezone.now()
        else:
            now = probe.time
        if now < withdrawal_threshold:
            raise WithdrawalThresholdNotReachedError

        if probe is not None:
            self.latest_recieved_probe_time = probe.time

    @transition(field=state, source=State.POTENTIAL_DEPARTURE, target=State.ARRIVAL)
    def probe_detected(self, probe):
        self.latest_recieved_probe_time = probe.time

    @transition(field=state, source=State.POTENTIAL_DEPARTURE, target=State.DEPARTURE)
    def departure_threshold(self, probe=None):
        """"""
        departure_threshold = self.latest_recieved_probe_time + timezone.timedelta(
            seconds=self.burst_interval // 2)
        if probe is None:
            now = timezone.localtime()
        else:
            now = probe.time
        if now < departure_threshold:
            raise DepartureThreshholdNotReachedError

        add_departure(self, now)

    @transition(field=state, source=State.DEPARTURE, target=State.INITIAL)
    def initial(self):
        """User has departed. Return to initial state."""
        pass

    def __str__(self):
        return self.mac.format(default_dialect())


def add_arrival(mac: WifiInfo, time: timezone.datetime):
    try:
        mac.student
    except ObjectDoesNotExist:
        logger.warning(f"MAC {mac!r} has no student associated with it!")
        return

    logger.debug(f"Try to add arrival for student {mac.student!r}")
    for course in mac.student.courses.all():
        csa, _ = course.coursestudentattendance_set.get_or_create(student=mac.student)
        existing_record = csa.attendance_dates.filter(departure=None)
        if not existing_record:
            csa.attendance_dates.create(arrival=time)
            logger.debug(f"{mac!r}: Create Arrival at {time}")
        else:
            logger.debug(f"{mac!r}: Arrival already registered: {existing_record}")


def add_departure(mac: WifiInfo, time: timezone.datetime):
    try:
        mac.student
    except ObjectDoesNotExist:
        logger.warning(f"MAC {mac!r} has no student associated with it!")
        return

    logger.debug(f"Try to add departure for student {mac.student!r}")
    for course in mac.student.courses.all():
        csa, _ = course.coursestudentattendance_set.get_or_create(student=mac.student)
        existing_record = csa.attendance_dates.filter(departure=None)
        for attendance in existing_record:
            attendance.departure = time
            for day in course.start_times.all():
                course_start_time = day.get_this_weeks_date()
                course_end_time = course_start_time + timezone.timedelta(minutes=course.duration)
                start = course_start_time if course_start_time > attendance.arrival else attendance.arrival
                end = time if time < course_end_time else course_end_time
                time_present = end - start
                if time_present.total_seconds() > 0 and time_present.seconds <= course.duration*60:
                    attendance.time_present += time_present.seconds

            attendance.save()
            logger.debug(f"{mac!r}: Add departure at {time} for student {mac.student} and course {course}.")
            logger.debug(f"{mac!r}: {attendance!r}")


class Teacher(BaseUpdatingModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    additional_courses = models.ManyToManyField('Course', related_name='additional_teachers')

    @property
    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        return str(self.user)


class Probemon(BaseUpdatingModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    def create_user(self, email_suffix: str = '@probemon.com'):
        user_uuid = uuid.uuid4().hex[:30]
        user_email = user_uuid + email_suffix
        user_pw = User.objects.make_random_password()
        user = User.objects.create_user(user_email, user_pw)
        Token.objects.get_or_create(user=user)
        self.user = user

    @property
    def token(self):
        return self.user.auth_token

    def __str__(self):
        return str(self.user)
