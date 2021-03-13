from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import forms
from ..forms import CustomUserCreationForm, CustomUserChangeForm
from .. import models

class WeekDayInline(admin.TabularInline):
    model = models.WeekDay
    extra = 1


class CourseInline(admin.TabularInline):
    model = models.Course
    extra = 0


# Register your models here.
@admin.register(models.User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = models.User
    list_display = ['email', 'username']


@admin.register(models.Course,)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'min_attend_time', 'teacher')
    model = models.Course
    inlines = [
        WeekDayInline,
    ]
    form = forms.CourseAdminForm


@admin.register(models.Teacher)
class TeacherAdmin(admin.ModelAdmin):
    model = models.Teacher
    list_display = ['user', 'courses_display']
    inlines = [CourseInline]
    # fields = ('user', 'courses', 'additinal_courses')

    def courses_display(self, obj):
        return ", ".join([
            course.name for course in obj.courses.all()
        ])
    courses_display.short_description = "Courses"


@admin.register(models.Student)
class StudentAdmin(admin.ModelAdmin):
    model = models.Student
    form = forms.StudentAdminForm


admin.site.register((models.WeekDay, models.AccessToken, models.CourseStudentAttendance))
