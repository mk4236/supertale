from django.db import models
from django.conf import settings
from supertone.choices import LanguageType, ModelType, VoiceStyleType


class Voice(models.Model):
    name = models.CharField(max_length=100)
    voice_id = models.CharField(max_length=100, primary_key=True)
    styles = models.JSONField(default=dict)
    gender = models.CharField(max_length=20, blank=True, null=True)
    age = models.CharField(max_length=20, blank=True, null=True)
    user_case = models.CharField(max_length=50, blank=True, null=True)
    samples = models.JSONField(default=list)
    description = models.TextField(blank=True, null=True)
    thumbnail_image_url = models.URLField(blank=True, null=True)
    models = models.JSONField(default=list)

    def __str__(self):
        return self.name


class VoiceStyle(models.Model):
    name = models.CharField(max_length=100)
    style_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SuperTone(models.Model):
    title = models.CharField(max_length=200)
    contents = models.TextField()

    # -- TTS 공통 필드 시작 --
    voice = models.ForeignKey(
        Voice,
        to_field="voice_id",
        db_column="voice_id",
        on_delete=models.PROTECT,
        default="e5f6fb1a53d0add87afb4f",
    )
    style = models.CharField(
        max_length=50,
        default=VoiceStyleType.NEUTRAL,
    )
    language = models.CharField(
        max_length=10,
        choices=LanguageType.choices,
        default=LanguageType.KO,
    )
    model = models.CharField(
        max_length=30,
        choices=ModelType.choices,
        default=ModelType.SONA_SPEECH_1,
    )

    # 음성 생성 추가 파라미터
    pitch_shift = models.IntegerField(
        default=0,
        help_text="음정의 높낮이를 조정합니다. 0은 원래 보이스 음정이며 ±12까지 가능합니다.",
    )
    pitch_variance = models.FloatField(
        default=1,
        help_text="발화 중 억양 변화 정도를 조절합니다. 0.1~2 사이의 값을 가집니다.",
    )
    speed = models.FloatField(
        default=1, help_text="발화 속도를 조절합니다. 0.5~2 사이의 값을 가집니다."
    )

    audio_file = models.FileField(upload_to="supertone/audio/", null=True, blank=True)

    text = models.TextField()
    # -- TTS 공통 필드 끝 --

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="supertone_created",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="supertone_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title


class SuperToneLine(models.Model):
    supertone = models.ForeignKey(
        SuperTone, related_name="lines", on_delete=models.CASCADE
    )
    text = models.TextField()
    voice = models.ForeignKey(
        Voice,
        to_field="voice_id",  # 참조할 필드
        db_column="voice_id",  # 실제 DB 컬럼명도 맞춰줍니다
        on_delete=models.PROTECT,
        default="e5f6fb1a53d0add87afb4f",
    )
    style = models.CharField(
        max_length=50,
        default=VoiceStyleType.NEUTRAL,
    )
    language = models.CharField(
        max_length=10,
        choices=LanguageType.choices,
        default=LanguageType.KO,
    )
    model = models.CharField(
        max_length=30,
        choices=ModelType.choices,
        default=ModelType.SONA_SPEECH_1,
    )
    order = models.PositiveIntegerField()
    audio_file = models.FileField(upload_to="supertone/audio/", null=True, blank=True)
    # 음성 생성 추가 파라미터
    pitch_shift = models.IntegerField(
        default=0,
        help_text="음정의 높낮이를 조정합니다. 0은 원래 보이스 음정이며 ±12까지 가능합니다.",
    )
    pitch_variance = models.FloatField(
        default=1,
        help_text="발화 중 억양 변화 정도를 조절합니다. 0.1~2 사이의 값을 가집니다.",
    )
    speed = models.FloatField(
        default=1, help_text="발화 속도를 조절합니다. 0.5~2 사이의 값을 가집니다."
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.order}: {self.text}"
