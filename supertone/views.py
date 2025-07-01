import json
import logging
import re

import os
import zipfile
from io import BytesIO

import httpx
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import (
    HttpResponse,
    JsonResponse,
    StreamingHttpResponse,
    HttpResponseNotAllowed,
)
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.core.paginator import Paginator

from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)

from supertone.forms import SuperToneCreateForm, SuperToneUpdateForm

from supertone.choices import LanguageType, ModelType, UseCase, VoiceStyleType
from .models import SuperTone, Voice
from .models import SuperToneLine

from django.shortcuts import get_object_or_404
from io import BytesIO
from pydub import AudioSegment

AudioSegment.converter = "/usr/bin/ffmpeg"


def merge_audio(request, pk):
    """
    주어진 SuperTone(pk)에 속한 모든 라인 오디오를 order 순서대로 합쳐서
    single MP3 파일로 반환합니다.
    """
    # 1) 라인들을 순서대로 불러오기
    lines = SuperToneLine.objects.filter(supertone_id=pk).order_by("order")

    # 2) 첫 번째 오디오로 초기화
    merged = None
    for line in lines:
        if not line.audio_file:
            continue  # 오디오 없는 라인은 건너뛰기
        # storage에서 파일 읽기
        audio_path = line.audio_file.path
        segment = AudioSegment.from_file(audio_path)
        if merged is None:
            merged = segment
        else:
            merged += segment  # 이어붙이기

    if merged is None:
        return HttpResponse("합칠 오디오가 없습니다.", status=404)

    # 3) 메모리 버퍼에 MP3로 내보내기
    buf = BytesIO()
    merged.export(buf, format="mp3")
    buf.seek(0)

    # 4) 응답 생성
    filename = f"supertone_{pk}_merged.mp3"
    resp = HttpResponse(buf.read(), content_type="audio/mpeg")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


# 다운로드: 모든 라인 오디오 ZIP으로 묶어 반환
def download_zip(request, pk):
    """
    주어진 SuperTone(pk)에 속한 모든 라인 오디오 파일을 ZIP으로 묶어 반환합니다.
    """
    lines = SuperToneLine.objects.filter(supertone_id=pk).order_by("order")
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for line in lines:
            if not line.audio_file:
                continue
            file_path = line.audio_file.path
            arcname = os.path.basename(file_path)
            zipf.write(file_path, arcname)
    buffer.seek(0)
    filename = f"supertone_{pk}_audio.zip"
    resp = HttpResponse(buffer.read(), content_type="application/zip")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


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
        content = form.cleaned_data.get("contents", "")
        # Split but keep periods and question marks at end of segments, and split on newlines or quotes
        raw_segments = re.split(r'(?<=[\.?])\s*|[\r\n"]+', content)
        # Extract TTS parameters for each line
        voice = form.cleaned_data.get("voice")
        style = form.cleaned_data.get("style")
        language = form.cleaned_data.get("language")
        model_type = form.cleaned_data.get("model")
        pitch_shift = form.cleaned_data.get("pitch_shift")
        pitch_variance = form.cleaned_data.get("pitch_variance")
        speed = form.cleaned_data.get("speed")
        for idx, seg in enumerate(raw_segments, start=1):
            text = seg.strip()
            # Skip empty segments or segments containing only punctuation (., !, ?, ", ')
            if not text or re.fullmatch(r'^[\.\!\?\'"]+$', text):
                continue
            SuperToneLine.objects.create(
                supertone=self.object,
                text=text,
                order=idx,
                voice=voice,
                style=style,
                language=language,
                model=model_type,
                pitch_shift=pitch_shift,
                pitch_variance=pitch_variance,
                speed=speed,
            )
        return response

    def get_success_url(self):
        return reverse("supertone_update", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # 전체 Voice 객체를 템플릿에 넘겨줍니다
        ctx["voice_list"] = Voice.objects.all()
        ctx["voice_styles"] = VoiceStyleType.choices
        ctx["user_cases"] = UseCase.choices
        from django.core.paginator import Paginator

        # Initial modal voices listing (all voices, first page)
        paginator = Paginator(ctx["voice_list"], 10)
        ctx["voices"] = paginator.get_page(1)
        ctx["q"] = ""
        ctx["style"] = ""
        return ctx


class SuperToneUpdateView(LoginRequiredMixin, UpdateView):
    form_class = SuperToneUpdateForm
    model = SuperTone
    # fields = ["title"]
    template_name = "supertone/update.html"
    # success_url = reverse_lazy("supertone_list")

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "제목이 성공적으로 수정되었습니다.")
        return response

    def get_success_url(self):
        # After updating, reload the same update page instead of redirecting to list
        return reverse("supertone_update", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # 전체 Voice 객체를 템플릿에 넘겨줍니다
        ctx["voice_list"] = Voice.objects.all()

        # 스타일 및 사용처 선택을 위한 컨텍스트
        ctx["voice_styles"] = VoiceStyleType.choices
        ctx["user_cases"] = UseCase.choices

        # 모달 초기 표시용 검색 필터
        from django.core.paginator import Paginator

        paginator = Paginator(ctx["voice_list"], 10)
        ctx["voices"] = paginator.get_page(1)
        ctx["q"] = ""
        ctx["style"] = ""
        ctx["gender"] = ""
        ctx["user_case"] = ""
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
    pitch_shift = data.get("pitch_shift", 0)
    pitch_variance = data.get("pitch_variance", 1)
    speed = data.get("speed", 1)
    # Prepare payload for TTS API
    payload = {
        "text": text,
        "language": language,
        "style": style,
        "model": model,
        "voice_settings": {
            "pitch_shift": pitch_shift,
            "pitch_variance": pitch_variance,
            "speed": speed,
        },
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
        file_saved = False
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
                line.pitch_shift = pitch_shift
                line.pitch_variance = pitch_variance
                line.speed = speed
                line.save()
                # Save audio content to the line’s audio_file field
                timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
                # Save with line_id first, then timestamp
                filename = f"{line_id}_{timestamp}.wav"
                line.audio_file.save(filename, ContentFile(response.content), save=True)
                file_saved = True
            except SuperToneLine.DoesNotExist:
                logger.warning(f"SuperToneLine with id {line_id} not found")
        # Return the audio stream synchronously for now
        resp = HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "audio/wav"),
        )
        if file_saved:
            resp["X-File-Saved"] = "true"
        resp["Access-Control-Allow-Origin"] = "*"
        return resp
    except Exception as exc:
        logger.exception("Unexpected error in tts_proxy")
        resp = JsonResponse({"error": "서버 내부 오류", "detail": str(exc)}, status=500)
        resp["Access-Control-Allow-Origin"] = "*"
        return resp


@csrf_exempt
@require_http_methods(["OPTIONS", "POST"])
def tts_proxy_preview(request):
    """
    CORS-enabled TTS proxy that returns audio only, without saving to the database.
    """
    # Handle CORS preflight
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

    data = json.loads(request.body.decode("utf-8") or "{}")
    voice_id = data.get("voice_id", settings.SUPERTONE_VOICE_ID)
    text = data.get("text")
    language = data.get("language", LanguageType.KO)
    style = data.get("style", VoiceStyleType.NEUTRAL)
    model = data.get("model", ModelType.SONA_SPEECH_1)
    pitch_shift = data.get("pitch_shift", 0)
    pitch_variance = data.get("pitch_variance", 1)
    speed = data.get("speed", 1)

    if not voice_id or not text:
        resp = JsonResponse(
            {"error": "voice_id와 text를 모두 설정해야 합니다."}, status=400
        )
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

    payload = {
        "text": text,
        "language": language,
        "style": style,
        "model": model,
        "voice_settings": {
            "pitch_shift": pitch_shift,
            "pitch_variance": pitch_variance,
            "speed": speed,
        },
    }
    headers = {
        "Content-Type": "application/json",
        "x-sup-api-key": settings.SUPERTONE_API_KEY,
    }
    url = f"https://supertoneapi.com/v1/text-to-speech/{voice_id}"
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=60)
        if response.status_code >= 400:
            resp = JsonResponse(
                {
                    "error": "TTS 호출 실패",
                    "status": response.status_code,
                    "detail": response.text,
                },
                status=502,
            )
            resp["Access-Control-Allow-Origin"] = "*"
            return resp
        # return raw audio
        resp = HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "audio/wav"),
        )
        resp["Access-Control-Allow-Origin"] = "*"
        return resp
    except Exception as exc:
        logger.exception("Unexpected error in tts_proxy_preview")
        resp = JsonResponse({"error": "서버 내부 오류", "detail": str(exc)}, status=500)
        resp["Access-Control-Allow-Origin"] = "*"
        return resp


# --- Voice search view for AJAX/modal with filters and pagination ---
def voice_search(request):
    """
    AJAX/Modal voice search with filters and pagination.
    """
    q = request.GET.get("q", "")
    style = request.GET.get("style", "")
    gender = request.GET.get("gender", "")
    age = request.GET.get("age", "")
    user_case = request.GET.get("user_case", "")
    page_number = request.GET.get("page", 1)

    # Base queryset of all voices
    qs = Voice.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    if style:
        # Assuming 'styles' is a JSONField containing a list of style keys
        qs = qs.filter(styles__contains=[style])
    if gender:
        qs = qs.filter(gender=gender)
    if user_case:
        qs = qs.filter(user_case=user_case)
    if age:
        qs = qs.filter(age=age)

    paginator = Paginator(qs, 10)  # 10 items per page
    voices = paginator.get_page(page_number)

    return render(
        request,
        "supertone/voice_search_modal.html",
        {
            "voices": voices,
            "q": q,
            "style": style,
            "user_case": user_case,
            "gender": gender,
            "voice_styles": VoiceStyleType.choices,
            "user_cases": UseCase.choices,
        },
    )
