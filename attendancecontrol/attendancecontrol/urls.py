"""attendancecontrol URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from rest_framework import routers
from control.views import students, teachers, control
from probes_api import views as probes_views

api_router = routers.DefaultRouter()
api_router.register(r'probes', probes_views.ProbeRequestViewSet)

urlpatterns = [
    path('', control.redirect_root),
    path('control/', include('control.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/password/', auth_views.PasswordChangeView.as_view(
        template_name='registration/change_password.html',
        success_url='/',
    ), name='change_password'),
    path('accounts/signup/', control.SignUpView.as_view(), name='signup'),
    path('accounts/signup/student/', students.StudentSignUpView.as_view(), name='student_signup'),
    path('accounts/signup/teacher/', teachers.TeacherSignUpView.as_view(), name='teacher_signup'),
    path('qr_code/', include('qr_code.urls', namespace="qr_code")),
    # API URLS
    path('api-probes/', include(api_router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
