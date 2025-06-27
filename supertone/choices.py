from django.db import models


class LanguageType(models.TextChoices):
    """
    Enumeration of supported language codes.
    """

    KO = "ko", "Korean"
    EN = "en", "English"
    JP = "jp", "Japanese"


class ModelType(models.TextChoices):
    """
    Enumeration of supported model codes.
    """

    SONA_SPEECH_1 = "sona_speech_1", "Sona Speech 1"


class VoiceStyleType(models.TextChoices):
    """
    Enumeration of supported voice style codes.
    """

    NEUTRAL = "neutral", "일반"
    HAPPY = "happy", "기쁨"
    SERENE = "serene", "고요한"
