from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView, DeleteView, UpdateView
from django.urls import reverse, reverse_lazy

from ..decorators import teacher_required
from ..forms import TeacherSignUpForm, CourseCreateForm, WeekDaysFormSet, CourseWeekDaysFormSet
from ..models import User, Course, WeekDay, AccessToken


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
    template_name = 'teachers/teacher.html'

    def get_queryset(self):
        teacher = self.request.user.teacher
        return teacher.courses.all()


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCourseDetail(DetailView):
    context_object_name = 'course'
    template_name = 'teachers/course.html'

    def get_queryset(self):
        return self.request.user.teacher.courses.all()


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCreateCourse(CreateView):
    model = Course
    form_class = CourseCreateForm
    template_name = 'teachers/course_add_form.html'

    def get_success_url(self):
        return reverse('teacher:courses')

    def form_valid(self, form):
        ctx = self.get_context_data()
        formset = ctx['week_days_formset']
        if formset.is_valid() and form.is_valid():
            self.object = form.save()
            for weekday_data in formset.cleaned_data:
                if not weekday_data:
                    continue
                weekday, _ = WeekDay.objects.get_or_create(
                    day=weekday_data['day'], time=weekday_data['time']
                )
                weekday.save()
                self.object.start_times.add(weekday)
            self.request.user.teacher.courses.add(self.object)
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['form'] = CourseCreateForm(self.request.POST)
            ctx['week_days_formset'] = WeekDaysFormSet(self.request.POST, prefix="week_days")
        else:
            ctx['form'] = CourseCreateForm()
            ctx['week_days_formset'] = WeekDaysFormSet(prefix="week_days")
        return ctx


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherEditCourse(UpdateView):
    model = Course
    # form_class = CourseCreateForm
    fields = ['name', 'min_attend_time', 'duration']
    template_name = 'teachers/course_update_form.html'

    def get_success_url(self):
        return reverse('teacher:courses')

    def form_valid(self, form):
        ctx = self.get_context_data()
        formset = ctx['week_days_formset']
        if formset.is_valid() and form.is_valid():
            self.object = form.save()
            course_days = []
            for weekday_form in formset.forms:
                item = weekday_form.save(commit=False)
                if item is None or item.time is None:
                    continue
                item.save()
                course_days.append(item)
                self.object.start_times.add(item)
            self.object.start_times.clear()
            self.object.start_times.set(course_days)

            if self.object not in self.request.user.teacher.courses.all():
                self.request.user.teacher.courses.add(self.object)
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['week_days_formset'] = CourseWeekDaysFormSet(
                self.request.POST,
                queryset=self.object.start_times.all(),
                prefix="week_days"
            )
        else:
            ctx['week_days_formset'] = CourseWeekDaysFormSet(
                prefix="week_days", queryset=self.object.start_times.all()
            )
        return ctx


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCourseDelete(DeleteView):
    model = Course

    def get_success_url(self) -> str:
        return reverse_lazy('teacher:courses')

    def get_queryset(self):
        return self.request.user.teacher.courses.all()


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherEdit(UpdateView):
    model = User
    # form_class = TeacherUpdateForm
    fields = ('email', 'first_name', 'last_name')
    template_name = 'account_update_form.html'

    def get_success_url(self):
        return reverse('teacher:courses')


@login_required
@teacher_required
def set_access_token(request, pk):
    teachers_courses = request.user.teacher.courses.all()
    course = get_object_or_404(Course, pk=pk)

    if course in teachers_courses:
        token = AccessToken.objects.create(valid_time=course.duration)
        token.save()
        course.access_token = token
        course.save()

        expires = token.created + timedelta(seconds=token.valid_time*60)
        url = request.build_absolute_uri(course.get_absolute_student_register_url())

        context = {
            'id': course.id,
            'token': token.token,
            'expires': expires,
            'register_url': url
        }
        return render(request, 'teachers/course_registration.html', context=context)
    else:
        return HttpResponseForbidden()
