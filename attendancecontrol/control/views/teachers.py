from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView

from ..decorators import teacher_required
from ..forms import TeacherSignUpForm
from ..models import User, Course


class TeacherSignUpView(CreateView):
    model = User
    form_class = TeacherSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'teacher'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('teachers:courses')


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCoursesList(ListView):
    model = Course
    ordering = ('name', )
    context_object_name = 'courses'
    template_name = 'control/courses_list.html'

    def get_queryset(self):
        teacher = self.request.user.teacher
        return teacher.courses.all()
