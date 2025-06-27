from django import forms
from .models import SuperTone


class SuperToneCreateForm(forms.ModelForm):
    class Meta:
        model = SuperTone
        fields = [
            "title",
            "contents",
            "text",
            "voice",
            "style",
            "language",
            "model",
            "pitch_shift",
            "pitch_variance",
            "speed",
        ]
        labels = {
            "title": "제목",
            "text": "미리듣기 내용",
            "contents": "본문 내용",
            "voice": "음성",
            "style": "스타일",
            "language": "언어",
            "model": "모델",
            "pitch_shift": "음정 조정",
            "pitch_variance": "억양 변화",
            "speed": "속도",
        }
        widgets = {
            "text": forms.Textarea(attrs={"rows": 4}),
        }


class SuperToneUpdateForm(forms.ModelForm):
    class Meta:
        model = SuperTone
        fields = [
            "title",
            "voice",
            "text",
            "style",
            "language",
            "model",
            "pitch_shift",
            "pitch_variance",
            "speed",
        ]
        labels = {
            "text": "미리듣기 내용",
            "title": "제목",
            "voice": "음성",
            "style": "스타일",
            "language": "언어",
            "model": "모델",
            "pitch_shift": "음정 조정",
            "pitch_variance": "억양 변화",
            "speed": "속도",
        }
