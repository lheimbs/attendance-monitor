from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView, DeleteView, UpdateView
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from .. import forms
from ..decorators import teacher_required
from ..models import User, Course, WeekDay, AccessToken


class TeacherSignUpView(CreateView):
    model = User
    form_class = forms.TeacherSignUpForm
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
        return self.request.user.teacher.courses.all()


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCourseDetail(DetailView):
    context_object_name = 'course'
    template_name = 'teachers/course.html'

    def get_queryset(self):
        return self.request.user.teacher.courses.all()


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCreateCourse(CreateView):
    model = Course
    form_class = forms.CourseCreateForm
    template_name = 'teachers/course_add_form.html'

    def get_success_url(self):
        return reverse('teacher:courses')

    def form_valid(self, form):
        ctx = self.get_context_data()
        formset = ctx['week_days_formset']
        if formset.is_valid() and form.is_valid():
            self.object = form.save()
            for weekday_data in formset.cleaned_data:
                weekday = WeekDay.objects.create(
                    day=weekday_data['day'], time=weekday_data['time']
                )
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
            ctx['form'] = forms.CourseCreateForm(self.request.POST)
            ctx['week_days_formset'] = forms.WeekDaysFormSet(self.request.POST, prefix="week_days")
        else:
            ctx['form'] = forms.CourseCreateForm()
            ctx['week_days_formset'] = forms.WeekDaysFormSet(prefix="week_days")
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
            form.save()
            formset.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['week_days_formset'] = forms.CourseWeekDaysInlineFormSet(
                self.request.POST,
                queryset=self.object.start_times.all(),
                instance=self.object,
                prefix="week_days"
            )
        else:
            ctx['week_days_formset'] = forms.CourseWeekDaysInlineFormSet(
                prefix="week_days", instance=self.object, queryset=self.object.start_times.all()
            )
        return ctx


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCourseDelete(DeleteView):
    # TODO: make this into modal (bit more elegant?)
    model = Course
    template_name = 'course_confirm_delete.html'

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

    # TODO: use UserPassesTestMixin instead of limiting queryset to return forbidden?
    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.id)

    def get_success_url(self):
        return reverse('teacher:courses')


@login_required
@teacher_required
def set_access_token(request, pk):
    course = get_object_or_404(request.user.teacher.courses.filter(pk=pk))

    token = AccessToken.objects.create(valid_time=course.duration)
    token.save()
    course.access_token = token
    course.save()

    expires = token.created + timezone.timedelta(seconds=token.valid_time*60)
    url = request.build_absolute_uri(course.get_absolute_student_register_url())

    context = {
        'id': course.id,
        'token': token.token,
        'expires': expires,
        'register_url': url
    }
    return render(request, 'teachers/course_registration.html', context=context)
