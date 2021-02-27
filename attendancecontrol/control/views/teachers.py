from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView

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
        return redirect('teacher:courses')


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCoursesList(ListView):
    model = Course
    ordering = ('name', )
    context_object_name = 'courses'
    template_name = 'control/teachers/teacher.html'

    def get_queryset(self):
        teacher = self.request.user.teacher
        return teacher.courses.all()


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCourseDetail(DetailView):
    context_object_name = 'course'
    template_name = 'control/teachers/course.html'

    def get_queryset(self):
        return self.request.user.teacher.courses.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course_obj_url'] = self.request.build_absolute_uri(
            self.object.get_absolute_student_url()
        )
        return context

@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCreateCourse(CreateView):
    model = Course
    fields = ['name', 'min_attend_time', 'duration', 'start_times']
