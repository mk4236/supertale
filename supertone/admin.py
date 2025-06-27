from django.contrib import admin
from .models import SuperTone, Voice, SuperToneLine


@admin.register(SuperTone)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "updated_at", "created_by", "updated_by")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Voice)
class VoiceAdmin(admin.ModelAdmin):
    list_display = ("name", "voice_id")


@admin.register(SuperToneLine)
class SuperToneLineAdmin(admin.ModelAdmin):
    list_display = ("supertone", "order", "text", "voice", "style", "language", "model")
    ordering = ("supertone", "order")
