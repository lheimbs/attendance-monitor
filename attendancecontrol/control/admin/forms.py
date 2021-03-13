from django import forms
from django.utils import timezone

from .. import models

class StudentAdminForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=models.Course.objects.all(),
        required=False,
    )

    class Meta:
        model = models.Student
        fields = '__all__'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['courses'].initial = self.instance.courses.all()

    def save(self, commit=True):
        student = super().save(commit=False)
        if commit:
            student.save()

        if student.pk:
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
