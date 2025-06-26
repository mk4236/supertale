from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView

urlpatterns = [
    # 로그인/로그아웃
    path(
        "login/",
        CustomLoginView.as_view(),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # 회원가입
    path("signup/", views.SignUpView.as_view(), name="signup"),
]
