from django import forms
from django.contrib import admin
from django.utils import timezone

from macaddress.formfields import MACAddressField

from .. import models


class WifiInfoInline(admin.TabularInline):
    model = models.WifiInfo
    fields = ('mac',)


class StudentAdminForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=models.Course.objects.all(),
        required=False,
    )
    mac = MACAddressField(help_text="Your phones MAC Address")

    class Meta:
        model = models.Student
        fields = ('user', 'student_nr')

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['courses'].initial = self.instance.courses.all()
            mac = self.instance.wifi_info.mac if self.instance.wifi_info else ''
            self.fields['mac'].initial = mac

    def save(self, commit=True):
        student = super().save(commit=False)
        if commit:
            student.save()

        if student.pk:
            if student.wifi_info and student.wifi_info.mac != self.cleaned_data['mac']:
                student.wifi_info.mac = self.cleaned_data['mac']
            else:
                student.wifi_info = models.WifiInfo.objects.create(mac=self.cleaned_data['mac'])
            student.courses.set(
                self.cleaned_data['courses'],
                through_defaults={'created': timezone.now(), 'modified': timezone.now()}
            )
            self.save_m2m()
        return student


class CourseAdminForm(forms.ModelForm):
    additional_teachers = forms.ModelMultipleChoiceField(
        queryset=models.Teacher.objects.none(),
        required=False,
    )

    class Meta:
        model = models.Course
        fields = '__all__'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['additional_teachers'].initial = self.instance.additional_teachers.all()
            if self.instance.teacher:
                self.fields['additional_teachers'].queryset = models.Teacher.objects.exclude(
                    pk=self.instance.teacher.user.id
                )

    def save(self, commit=True):
        course = super().save(commit=False)

        if commit:
            course.save()

        if course.pk:
            new_additional_teachers = self.cleaned_data['additional_teachers']
            # if self.instance.teacher in new_additional_teachers:
            #     new_additional_teachers.exclude(pk=self.instance.teacher.user.id)
            course.additional_teachers.set(
                new_additional_teachers, through_defaults={'created': timezone.now(), 'modified': timezone.now()}
            )
            self.save_m2m()
        return course
