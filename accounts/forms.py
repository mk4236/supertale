from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label="아이디",
        max_length=150,
        help_text="필수. 150자 이하. 문자, 숫자, @/./+/-/_ 만 가능합니다.",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    nickname = forms.CharField(
        label="이름",
        max_length=150,
        help_text="실제 이름을 입력하세요.",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    password1 = forms.CharField(
        label="비밀번호",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text="최소 8자 이상이어야 합니다.",
    )
    password2 = forms.CharField(
        label="비밀번호 확인",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text="위와 동일한 비밀번호를 입력하세요.",
    )

    class Meta:
        model = User
        fields = ("username", "nickname", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        # Store nickname in first_name field for real name
        user.first_name = self.cleaned_data["nickname"]
        if commit:
            user.save()
        return user


# Custom Authentication Form
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="아이디",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="패스워드",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
