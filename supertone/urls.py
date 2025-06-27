from django.urls import path
from .views import (
    SuperToneListView,
    SuperToneDetailView,
    SuperToneCreateView,
    SuperToneUpdateView,
)
from . import views
from .views import download_zip

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
    path("tts_preview/", views.tts_proxy_preview, name="tts_proxy_preview"),
    path(
        "supertone/<int:pk>/merge-audio/",
        views.merge_audio,
        name="supertone_merge_audio",
    ),
    path(
        "<int:pk>/download-zip/",
        views.download_zip,
        name="supertone_download_zip",
    ),
]
