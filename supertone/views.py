import httpx
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, ListView, UpdateView

import logging
import json

logger = logging.getLogger(__name__)

from .models import SuperTone


class SuperToneListView(LoginRequiredMixin, ListView):
    model = SuperTone
    template_name = "supertone/list.html"
    context_object_name = "supertones"
    ordering = ["-created_at"]
    paginate_by = 20


class SuperToneDetailView(LoginRequiredMixin, DetailView):
    model = SuperTone
    template_name = "supertone/detail.html"
    context_object_name = "supertone"


class SuperToneCreateView(LoginRequiredMixin, CreateView):
    model = SuperTone
    fields = ["title", "contents"]
    template_name = "supertone/form.html"
    success_url = reverse_lazy("supertone_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class SuperToneUpdateView(LoginRequiredMixin, UpdateView):
    model = SuperTone
    fields = ["title", "contents"]
    template_name = "supertone/form.html"
    success_url = reverse_lazy("supertone_list")

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


@csrf_exempt
@require_http_methods(["OPTIONS", "POST"])
def tts_proxy(request):
    logger.debug(
        f"tts_proxy called, method={request.method}, body={request.body[:100]}"
    )
    # CORS preflight response
    if request.method == "OPTIONS":
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method != "POST":
        resp = JsonResponse({"error": "POST만 허용"}, status=405)
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

    # Parse incoming JSON and determine voice_id
    data = json.loads(request.body.decode("utf-8") or "{}")
    voice_id = data.get("voice_id", settings.SUPERTONE_VOICE_ID)
    if not voice_id:
        resp = JsonResponse({"error": "voice_id가 설정되지 않았습니다."}, status=400)
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

    headers = {
        "Content-Type": "application/json",
        "x-sup-api-key": settings.SUPERTONE_API_KEY,
    }
    url = f"https://supertoneapi.com/v1/text-to-speech/{voice_id}"
    try:
        logger.debug(f"Sending TTS request to {url} with payload: {data}")
        response = httpx.post(url, json=data, headers=headers, timeout=60)
        logger.debug(
            f"Received upstream response: status={response.status_code}, body={response.text[:200]}"
        )
        if response.status_code >= 400:
            resp = JsonResponse(
                {
                    "error": "TTS 호출 실패",
                    "status": response.status_code,
                    "url": url,
                    "payload": data,
                    "detail": response.text,
                },
                status=502,
            )
            resp["Access-Control-Allow-Origin"] = "*"
            return resp
        # Return the audio stream synchronously for now
        resp = HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "audio/wav"),
        )
        resp["Access-Control-Allow-Origin"] = "*"
        return resp
    except Exception as exc:
        logger.exception("Unexpected error in tts_proxy")
        resp = JsonResponse({"error": "서버 내부 오류", "detail": str(exc)}, status=500)
        resp["Access-Control-Allow-Origin"] = "*"
        return resp
