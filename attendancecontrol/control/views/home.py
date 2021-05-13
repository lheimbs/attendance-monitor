# from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import logout


# Create your views here.
def home(request):
    if request.user.is_authenticated and request.user.is_teacher:
        return redirect('teacher:courses')
    elif request.user.is_authenticated and request.user.is_student:
        return redirect('student:courses')
    elif request.user.is_authenticated:
        messages.add_message(request, messages.ERROR, (
            "You are neither a student nor a teacher. "
            "Please contact the administrator to assign your account a role or "
            "login with a different account.")
        )
        logout(request)
    return render(request, 'control/home.html')
