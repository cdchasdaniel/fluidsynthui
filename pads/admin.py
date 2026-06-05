from django.contrib import admin
from .models import Pad


@admin.register(Pad)
class PadAdmin(admin.ModelAdmin):
    list_display = ('name', 'file_name', 'preset', 'preset_name', 'velocity', 'updated_at')
    list_filter = ('file_name', 'velocity')
    search_fields = ('name', 'preset_name', 'file_name')
    readonly_fields = ('created_at', 'updated_at')
