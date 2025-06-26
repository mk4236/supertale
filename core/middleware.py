from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

EXEMPT_URLS = [
    reverse("login"),
    reverse("signup"),
    settings.LOGIN_URL,
    "/admin/login/",
    settings.STATIC_URL,
    settings.MEDIA_URL,
]


class LoginRequiredMiddleware:
    """
    비인증 사용자는 로그인 페이지로 리다이렉트합니다.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if not request.user.is_authenticated:
            if not any(path.startswith(u) for u in EXEMPT_URLS):
                return redirect(f"{settings.LOGIN_URL}?next={path}")
        return self.get_response(request)
