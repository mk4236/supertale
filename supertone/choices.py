from django.db import models


class LanguageType(models.TextChoices):
    """
    Enumeration of supported language codes.
    """

    KO = "ko", "Korean"
    EN = "en", "English"
    JP = "jp", "Japanese"


class UseCase(models.TextChoices):
    NARRATION = "narration", "나레이션"
    ADVERTISEMENT = "advertisement", "광고"
    EDUCATION = "education", "교육"
    AUDIOBOOK = "audiobook", "오디오북"
    DOCUMENTARY = "documentary", "다큐멘터리"
    GAME = "game", "게임"
    MEME = "meme", "밈"
    ANNOUNCEMENT = "announcement", "아나운서 톤"


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
    ACTIVE = "active", "활성"
    ACTIVE_PLUS = "active +", "활성 +"
    ADMIRING = "admiring", "감탄"
    ADMIRING_PLUS = "admiring +", "감탄 +"
    AMUSED = "amused", "즐거움"
    AMUSED_PLUS = "amused +", "즐거움 +"
    ANGRY = "angry", "화남"
    ANGRY_PLUS = "angry +", "화남 +"
    BLANK = "blank", "멍한"
    COMMAND = "command", "명령"
    CONFIDENT = "confident", "자신감"
    CONFUSED = "confused", "혼란"
    CONFUSED_PLUS = "confused +", "혼란 +"
    COURAGEOUS = "courageous", "용감"
    COURAGEOUS_PLUS = "courageous +", "용감 +"
    CURIOUS = "curious", "호기심"
    DISGUSTED = "disgusted", "역겨움"
    DISGUSTED_PLUS = "disgusted +", "역겨움 +"
    DOMINATING = "dominating", "지배"
    EMBARRASSED = "embarrassed", "당황"
    EMBARRASSED_PLUS = "embarrassed +", "당황 +"
    EVIL = "evil", "사악"
    EVIL_PLUS = "evil +", "사악 +"
    EXCITED = "excited", "신남"
    FRIENDLY = "friendly", "친근"
    FLIRTY = "flirty", "농염"
    HAPPY = "happy", "행복"
    HAPPY_PLUS = "happy +", "행복 +"
    JEALOUS = "jealous", "질투"
    JEALOUS_PLUS = "jealous +", "질투 +"
    KIND = "kind", "친절"
    LOVING = "loving", "사랑"
    LOVING_PLUS = "loving +", "사랑 +"
    NORMAL = "normal", "보통"
    PAINFUL = "painful", "고통"
    PAINFUL_PLUS = "painful +", "고통 +"
    SAD = "sad", "슬픔"
    SAD_PLUS = "sad +", "슬픔 +"
    SERENE = "serene", "평온"
    SHOUTING = "shouting", "고함"
    SHOUTING_PLUS = "shouting +", "고함 +"
    SHY = "shy", "수줍"
    SHY_PLUS = "shy +", "수줍 +"
    SLEEPY = "sleepy", "졸린"
    SOULLESS = "soulless", "무감정"
    SUSPICIOUS = "suspicious", "의심"
    SUSPICIOUS_PLUS = "suspicious +", "의심 +"
    SURPRISED = "surprised", "놀람"
    TEASING = "teasing", "장난"
    TEASING_PLUS = "teasing +", "장난 +"
    TRIUMPHANT = "triumphant", "승리감"
    TRIUMPHANT_PLUS = "triumphant +", "승리감 +"
    UNFRIENDLY = "unfriendly", "불친절"
    URGENT = "urgent", "긴급"
    WORRY = "worry", "걱정"
