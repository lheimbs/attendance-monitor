from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db import transaction
# from django.forms import fields
# from django.forms.utils import ValidationError
from macaddress.formfields import MACAddressField

from .models import Student, Teacher, User


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
        # student.interests.add(*self.cleaned_data.get('interests'))
        return user


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
