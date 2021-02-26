from django.views.generic import TemplateView
from django.http.response import HttpResponseRedirect
from django.urls import reverse

def redirect_root(request):
    return HttpResponseRedirect(reverse('home'))


class SignUpView(TemplateView):
    template_name = 'registration/signup.html'
