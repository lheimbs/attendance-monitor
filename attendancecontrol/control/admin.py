from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User, Student, Teacher, Course, WeekDay, AccessToken


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ['email', 'username']


# Register your models here.
admin.site.register(User, CustomUserAdmin)
admin.site.register((Student, Teacher, Course, WeekDay, AccessToken))
