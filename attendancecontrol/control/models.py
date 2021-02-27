from uuid import uuid4

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _
from macaddress.fields import MACAddressField


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
        user = self.model(email=email, **extra_fields)
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


# Create your models here.
class WeekDay(models.Model):
    MONDAY = 'MON'
    TUESDAY = 'TUE'
    WEDNESDAY = 'WED'
    THURSDAY = 'THU'
    FRIDAY = 'FRI'
    SATURDAY = 'SAT'
    SUNDAY = 'SUN'
    WEEKDAY_CHOICES = [
        (MONDAY, 'Monday'),
        (TUESDAY, 'Tuesday'),
        (WEDNESDAY, 'Wednesday'),
        (THURSDAY, 'Thursday'),
        (FRIDAY, 'Friday'),
        (SATURDAY, 'Saturday'),
        (SUNDAY, 'Sunday'),
    ]
    day = models.CharField(
        "course day",
        max_length=3,
        choices=WEEKDAY_CHOICES,
        default=MONDAY,
    )
    time = models.TimeField("starting time of course")

    def __str__(self):
        return "day: {}, time: {}".format(
            self.day, self.time
        )

class Course(models.Model):
    name = models.CharField("course name", max_length=200)
    uuid = models.UUIDField("course identifier", primary_key=False, unique=True, default=uuid4, editable=False)
    min_attend_time = models.IntegerField("minimum time present to count as attended in minutes", default=45)
    duration = models.IntegerField("course duration in minutes", default=90)
    start_times = models.ManyToManyField(WeekDay)
    is_ongoing = models.BooleanField(default=False)

    def get_absolute_student_url(self):
        from django.urls import reverse
        # user = self.request
        return reverse('students:detail', args=[str(self.id)])

    def get_absolute_teacher_url(self):
        from django.urls import reverse
        # user = self.request
        return reverse('teacher:detail', args=[str(self.id)])

    def __str__(self):
        return (
            f"name: {self.name}, "
            f"uuid: {self.uuid}, "
            f"min_attend_time: {self.min_attend_time}, "
            f"duration: {self.duration}"
        )


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    student_nr = models.IntegerField("matrikel nr")
    mac = MACAddressField(null=True, blank=True, integer=False)
    courses = models.ManyToManyField(Course)


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    courses = models.ManyToManyField(Course)
