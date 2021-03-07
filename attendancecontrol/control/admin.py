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
    model = Course
    inlines = [
        WeekDayInline,
    ]
    # fields = ['__all__']


# Register your models here.
admin.site.register((Student, Teacher, WeekDay, AccessToken))
