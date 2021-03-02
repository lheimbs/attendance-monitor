from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db import transaction
from macaddress.formfields import MACAddressField

from .models import Student, Teacher, User, Course, WeekDay


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email',)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email',)


class TeacherSignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.username = user.email
        user.is_teacher = True
        user.save()
        Teacher.objects.create(user=user)
        return user


class StudentUpdateForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email',)

    password = None
    student_nr = forms.IntegerField(label="Matrikel Nr.")
    mac = MACAddressField(label="MAC Address")


class StudentSignUpForm(CustomUserCreationForm):
    student_nr = forms.IntegerField(label="Matrikel Nr.")
    mac = MACAddressField(label="MAC Address")

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_student = True
        user.save()
        Student.objects.create(
            user=user,
            student_nr=self.cleaned_data.get('student_nr'),
            mac=self.cleaned_data.get('mac')
        )
        return user


class WeekDayCreateForm(forms.ModelForm):
    class Meta:
        model = WeekDay
        fields = ('day', 'time')


class CourseCreateForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'min_attend_time', 'duration']


WeekDaysFormSet = forms.formset_factory(
    WeekDayCreateForm, extra=1
)


CourseWeekDaysFormSet = forms.modelformset_factory(
    WeekDay, fields=('day', 'time'), extra=1, can_delete=True
)


class StudentCourseManualRegisrationForm(forms.Form):
    id = forms.IntegerField(label="Course ID")
    token = forms.CharField(max_length=30, min_length=10, label="Course Token")
