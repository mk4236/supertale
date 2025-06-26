from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView


from accounts.forms import CustomAuthenticationForm, CustomUserCreationForm


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("login")


class CustomLoginView(LoginView):
    """
    로그인 페이지에 CustomAuthenticationForm을 사용합니다.
    """

    template_name = "accounts/login.html"
    authentication_form = CustomAuthenticationForm
