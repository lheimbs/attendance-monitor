from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models.users import User, Student, Teacher
from .models.courses import Course, WeekDay, AccessToken


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ['email', 'username']


class WeekDayInline(admin.TabularInline):
    model = WeekDay
    extra = 1


@admin.register(Course,)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'min_attend_time', 'teacher')
    model = Course
    inlines = [
        WeekDayInline,
    ]
    # fields = ['__all__']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    model = Teacher
    list_display = ['user', 'courses_display']
    # fields = ('user', 'courses', 'additinal_courses')

    def courses_display(self, obj):
        return ", ".join([
            course.name for course in obj.courses.all()
        ])
    courses_display.short_description = "Courses"


# Register your models here.
admin.site.register((Student, WeekDay, AccessToken))
