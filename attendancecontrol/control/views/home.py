# from django.shortcuts import render
from django.shortcuts import render, redirect

# Create your views here.
def home(request):
    if request.user.is_authenticated and request.user.is_teacher:
        return redirect('teachers:courses')
    elif request.user.is_authenticated and request.user.is_student:
        return redirect('students:courses')
    return render(request, 'control/home.html')
