from django.urls import path
from .views import (
    SuperToneListView,
    SuperToneDetailView,
    SuperToneCreateView,
    SuperToneUpdateView,
)
from . import views

urlpatterns = [
    path("", SuperToneListView.as_view(), name="supertone_list"),
    path("<int:pk>/", SuperToneDetailView.as_view(), name="supertone_detail"),
    path("create/", SuperToneCreateView.as_view(), name="supertone_create"),
    path(
        "<int:pk>/update/",
        SuperToneUpdateView.as_view(),
        name="supertone_update",
    ),
    path("tts/", views.tts_proxy, name="tts_proxy"),
]
