from django.contrib import admin
from .models import SuperTone


@admin.register(SuperTone)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "updated_at", "created_by", "updated_by")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
