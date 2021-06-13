
import uuid
import logging

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder

from macaddress.fields import MACAddressField
from macaddress import default_dialect
from rest_framework.authtoken.models import Token
from django_fsm import FSMField, transition

from .base import BaseUpdatingModel

logger = logging.getLogger(__name__)

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
    mac_burst_interval = models.FloatField(default=60*60)   # one hour default
    mac_burst_count = models.PositiveIntegerField(default=0)
    mac_burst_updated = models.DateTimeField(blank=True, null=True)

    ARRIVAL_THRESHOLD = 60   # sixty seconds constant to differentiate probe bursts
    latest_recieved_probe_time = models.DateTimeField(blank=True, null=True)
    state = FSMField(max_length=50,
                     choices=State.CHOICES,
                     default=State.INITIAL_STATE,
                     protected=True)
    arrival_slot = models.JSONField(null=False, default=list, encoder=DjangoJSONEncoder)

    @transition(field=state, source=State.INITIAL, target=State.POTENTIAL_ARRIVAL)
    def initial_probe_detected(self, probe):
        """A probe request from this MAC address source is recieved.

        Advance to state 1 (potential arrival)."""
        print("State.INITIAL -> State.POTENTIAL_ARRIVAL")
        self.latest_recieved_probe_time = probe.time

    @transition(field=state, source=State.POTENTIAL_ARRIVAL, target=State.ARRIVAL)
    def arrival_threshold(self, probe):
        """A probe request from this MAC address source is detected again.

        Advance to ARRIVAL state if the probe came inside the arrival threshold time."""
        print("State.POTENTIAL_ARRIVAL -> State.ARRIVAL")
        arrival_threshold = self.latest_recieved_probe_time + timezone.timedelta(seconds=self.ARRIVAL_THRESHOLD)
        if probe.time > arrival_threshold:
            print("ArrivalThreshholdExceededError", probe.time, arrival_threshold)
            raise ArrivalThreshholdExceededError

        self.latest_recieved_probe_time = probe.time

    @transition(field=state, source=State.POTENTIAL_ARRIVAL, target=State.INITIAL)
    def withdrawal_threshold(self):
        """The ARRIVAL_THRESHOLD was exceeded. Return to initial state of SM."""
        print("State.POTENTIAL_ARRIVAL -> State.INITIAL")
        pass

    @transition(field=state, source=State.ARRIVAL, target=State.POTENTIAL_DEPARTURE)
    def without_probes_recently(self, probe=None):
        """Check if there were any probes recieved inside the departure threshold."""
        print("State.ARRIVAL -> State.POTENTIAL_DEPARTURE")
        withdrawal_threshold = self.latest_recieved_probe_time + timezone.timedelta(
            seconds=self.mac_burst_interval)
        if probe is None:
            now = timezone.now()
        else:
            now = probe.time
        if now < withdrawal_threshold:
            print("WithdrawalThresholdNotReachedError", now, withdrawal_threshold)
            raise WithdrawalThresholdNotReachedError

        if probe is not None:
            self.latest_recieved_probe_time = probe.time

    @transition(field=state, source=State.POTENTIAL_DEPARTURE, target=State.ARRIVAL)
    def probe_detected(self, probe):
        print("State.POTENTIAL_DEPARTURE -> State.ARRIVAL")
        self.latest_recieved_probe_time = probe.time

    @transition(field=state, source=State.POTENTIAL_DEPARTURE, target=State.DEPARTURE)
    def departure_threshold(self, probe=None):
        """"""
        print("State.POTENTIAL_DEPARTURE -> State.DEPARTURE")
        departure_threshold = self.latest_recieved_probe_time + timezone.timedelta(
            seconds=self.mac_burst_interval // 2)
        if probe is None:
            now = timezone.now()
        else:
            now = probe.time
        if now < departure_threshold:
            print("DepartureThreshholdNotReachedError", now, departure_threshold)
            raise DepartureThreshholdNotReachedError
        # self.initial()

    @transition(field=state, source=State.DEPARTURE, target=State.INITIAL)
    def initial(self):
        """User has departed. Return to initial state."""
        print("State.DEPARTURE -> State.INITIAL")
        pass

    def __str__(self):
        return self.mac.format(default_dialect())


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
