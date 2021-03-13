from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http.response import JsonResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.urls import reverse

from ..decorators import student_required
from ..forms import StudentSignUpForm, StudentCourseManualRegisrationForm, StudentUpdateForm
from ..models.users import User
from ..models.courses import Course


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
        return redirect('student:courses')


@method_decorator([login_required, student_required], name='dispatch')
class StudentEdit(UpdateView):
    model = User
    form_class = StudentUpdateForm
    template_name = 'control/account_update_form.html'

    # TODO: use UserPassesTestMixin instead of limiting queryset to return forbidden?
    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.id)

    def get_initial(self):
        initial = super().get_initial()
        initial['student_nr'] = self.request.user.student.student_nr
        initial['mac'] = self.request.user.student.mac
        return initial

    def get_success_url(self):
        return reverse('student:courses')

    def form_valid(self, form):
        self.object.student.student_nr = form.cleaned_data['student_nr']
        self.object.student.mac = form.cleaned_data['mac']
        self.object.student.save()
        return super().form_valid(form)


# TODO: remodel to show timetable with registered courses
@method_decorator([login_required, student_required], name='dispatch')
class StudentCoursesList(ListView):
    model = Course
    ordering = ('name', )
    context_object_name = 'courses'
    template_name = 'control/students/courses_list.html'

    def get_queryset(self):
        """Sort courses first by ongoing true then false and then ascending by id"""
        courses = self.request.user.student.courses.all()
        # not is_ongoing because: True > False
        return sorted(list(courses), key=lambda c: (not c.is_ongoing(), c.id))


@method_decorator([login_required, student_required], name='dispatch')
class StudentCourseDetail(DetailView):
    context_object_name = 'course'
    template_name = 'control/students/course.html'

    def get_queryset(self):
        return self.request.user.student.courses.all()


def authenticate_student_course(course, student, token):
    msg_type = messages.WARNING
    redirect_course = True
    is_authenticated = False

    # TODO: test for success not error!
    if student.courses.exists() and course in student.courses.all():
        msg_type = messages.INFO
        msg = "You are already registered to this course."
    elif not course.access_token:
        msg = "This course is not open for registrations!"
        redirect_course = False
    elif course.access_token.is_token_expired():
        msg = "This course is not open for registrations!"
        redirect_course = False
    elif not course.access_token.is_token_valid(token):
        msg = "Invalid Access Token!"
        redirect_course = False
    else:
        is_authenticated = True
        msg_type = messages.SUCCESS
        msg = "You successfully registered for this course."
    return is_authenticated, msg_type, msg, redirect_course


@login_required
@student_required
def register_student_for_course(request, pk, token):
    course = get_object_or_404(Course, pk=pk)
    is_authenticated, msg_type, msg, redirect_course = authenticate_student_course(
        course, request.user.student, token
    )
    if is_authenticated:
        request.user.student.courses.add(course, through_defaults={'created': timezone.now(), 'modified': timezone.now()})
    messages.add_message(request, msg_type, msg)
    return redirect('student:detail', pk) if redirect_course else redirect('student:courses')


@login_required
@student_required
def manual_register_student_for_course(request):
    if request.method == 'POST':
        form = StudentCourseManualRegisrationForm(request.POST)

        if form.is_valid():
            return redirect('student:register_course', form.cleaned_data['id'], form.cleaned_data['token'])
    else:
        form = StudentCourseManualRegisrationForm()

    context = {'form': form}
    return render(request, 'control/students/course_register.html', context)


@login_required
@student_required
def student_leave_course(request, pk):
    course = get_object_or_404(request.user.student.courses.filter(pk=pk))
    request.user.student.courses.remove(course)
    messages.add_message(request, messages.SUCCESS, f"You successfully left course {course.name}.")
    return redirect('student:courses')


@login_required
@student_required
def get_courses_states(request):
    courses = {}
    for course in request.user.student.courses.all():
        courses[course.id] = True if course.is_ongoing() else False
    return JsonResponse(courses)
