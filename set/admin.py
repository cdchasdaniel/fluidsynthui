from django.contrib import admin
from .models import Set, SetSong


class SetSongInline(admin.TabularInline):
    model = SetSong
    extra = 1
    autocomplete_fields = ['song']


@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'location')
    inlines = [SetSongInline]


@admin.register(SetSong)
class SetSongAdmin(admin.ModelAdmin):
    list_display = ('set', 'song', 'order')
    list_filter = ('set',)