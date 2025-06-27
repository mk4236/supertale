import json
import logging
import re

import httpx
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)

from supertone.forms import SuperToneCreateForm

from supertone.choices import LanguageType, ModelType, VoiceStyleType
from .models import SuperTone, Voice
from .models import SuperToneLine


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
    form_class = SuperToneCreateForm
    model = SuperTone
    template_name = "supertone/create.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        # Split contents and save each non-empty segment in order
        content = form.cleaned_data.get("contents", "")
        segments = [seg.strip() for seg in re.split(r"[.\n]+", content)]
        for idx, seg in enumerate(segments, start=1):
            if seg:
                SuperToneLine.objects.create(supertone=self.object, text=seg, order=idx)
        return response

    def get_success_url(self):
        return reverse("supertone_update", kwargs={"pk": self.object.pk})


class SuperToneUpdateView(LoginRequiredMixin, UpdateView):
    model = SuperTone
    fields = ["title", "contents"]
    template_name = "supertone/update.html"
    success_url = reverse_lazy("supertone_list")

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        # Update existing lines based on submitted inputs
        # Expect fields: step_<order>, voice_id_<order>, style_<order>, language_<order>, model_<order>
        for idx, line in enumerate(self.object.lines.order_by("order"), start=1):
            text = self.request.POST.get(f"step_{idx}", "").strip()
            if not text:
                # delete if empty
                line.delete()
                continue
            line.text = text
            line.voice_id = self.request.POST.get(f"voice_id_{idx}", line.voice_id)
            line.style = self.request.POST.get(f"style_{idx}", line.style)
            line.language = self.request.POST.get(f"language_{idx}", line.language)
            line.model = self.request.POST.get(f"model_{idx}", line.model)
            line.order = idx
            line.save()
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # 전체 Voice 객체를 템플릿에 넘겨줍니다
        ctx["voice_list"] = Voice.objects.all()
        ctx["voice_styles"] = VoiceStyleType.choices
        ctx["lines"] = self.object.lines.order_by("order")
        return ctx


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

    # Extract TTS parameters
    text = data.get("text")
    language = data.get("language", LanguageType.KO)
    style = data.get("style", VoiceStyleType.NEUTRAL)
    model = data.get("model", ModelType.SONA_SPEECH_1)
    # Prepare payload for TTS API
    payload = {
        "text": text,
        "language": language,
        "style": style,
        "model": model,
    }
    line_id = data.get("line_id")

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
        logger.debug(f"Sending TTS request to {url} with payload: {payload}")
        response = httpx.post(url, json=payload, headers=headers, timeout=60)
        logger.debug(
            f"Received upstream response: status={response.status_code}, body={response.text[:200]}"
        )
        if response.status_code >= 400:
            resp = JsonResponse(
                {
                    "error": "TTS 호출 실패",
                    "status": response.status_code,
                    "message": response.json().get("message", response.text),
                    "detail": response.text,
                },
                status=502,
            )
            resp["Access-Control-Allow-Origin"] = "*"
            return resp
        # If a line_id was provided, update the TTS parameters on the line
        if line_id:
            try:
                line = SuperToneLine.objects.get(pk=line_id)
                # Update TTS parameters on the line
                voice_obj = Voice.objects.get(voice_id=voice_id)
                line.voice = voice_obj
                line.style = style
                line.language = language
                line.model = model
                line.text = text
                line.save()
                # Save audio content to the line’s audio_file field
                timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
                filename = f"{timestamp}_{line_id}.wav"
                line.audio_file.save(filename, ContentFile(response.content), save=True)
            except SuperToneLine.DoesNotExist:
                logger.warning(f"SuperToneLine with id {line_id} not found")
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
