from django import forms
from .models import SuperTone


class SuperToneCreateForm(forms.ModelForm):
    class Meta:
        model = SuperTone
        fields = ["title", "contents"]
        labels = {
            "title": "제목",
            "contents": "내용",
        }


class SuperToneUpdateForm(forms.ModelForm):
    class Meta:
        model = SuperTone
        fields = ["title"]
        labels = {
            "title": "제목",
        }
