from django.contrib import admin
from .models import Song


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('name', 'tempo', 'patch', 'pad')
    search_fields = ('name',)
    ordering = ('name',)
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'tempo', 'time_signature', 'notes')
        }),
        ('Instruments & Effects', {
            'fields': ('patch', 'pad')
        }),
        ('Backing Tracks', {
            'fields': ('mp3_slot_1', 'mp3_slot_2', 'mp3_slot_3', 'mp3_slot_4',
                      'mp3_slot_5', 'mp3_slot_6', 'mp3_slot_7', 'mp3_slot_8'),
            'classes': ('collapse',)
        }),
    )
