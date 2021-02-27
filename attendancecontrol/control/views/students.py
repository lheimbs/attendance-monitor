from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView

from ..decorators import student_required
from ..forms import StudentSignUpForm
from ..models import User, Course


class StudentSignUpView(CreateView):
    model = User
    form_class = StudentSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('students:courses')


# TODO: remodel to show timetable with registered courses
@method_decorator([login_required, student_required], name='dispatch')
class StudentCoursesList(ListView):
    model = Course
    ordering = ('name', )
    context_object_name = 'courses'
    template_name = 'control/students/student.html'

    def get_queryset(self):
        student = self.request.user.student
        return student.courses.all()


@method_decorator([login_required, student_required], name='dispatch')
class StudentCourseDetail(DetailView):
    template_name = 'control/students/course.html'

    def get_queryset(self):
        return self.request.user.student.courses.all()
