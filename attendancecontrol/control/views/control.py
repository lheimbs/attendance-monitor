from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, redirect

def redirect_root(request):
    return HttpResponseRedirect(reverse('home'))


class SignUpView(TemplateView):
    template_name = 'registration/signup.html'


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'control/change_password.html', {
        'form': form
    })
