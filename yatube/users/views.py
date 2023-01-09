from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    """
    A View that manages sign up process of a user.
    """
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'
