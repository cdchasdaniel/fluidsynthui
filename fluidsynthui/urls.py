"""
URL configuration for fluidsynthui project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from patches import views as patches_view
from songs import views as songs_view
from set import views as sets_view
from pads import views as pads_view
from fluidsynthui import views as fluidsynthui_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', fluidsynthui_views.home, name='home'),
    path('patches/', patches_view.home, name='patches'),
    path('patch/add/', patches_view.add_patch, name='add_patch'),
    path('patch/edit/<int:pk>/', patches_view.add_patch, name='edit_patch'),
    path('patch/apply/<int:pk>/', patches_view.apply_patch, name='apply_patch'),
    path('patch/usage/<int:pk>/', patches_view.patch_usage, name='patch_usage'),
    path('get-presets-json/<str:sf_name>/', patches_view.get_presets_json, name='get_presets_json'),
    path('apply_patch_preview', patches_view.apply_patch_preview, name='apply_patch_preview'),
    path('songs', songs_view.home, name='songs'),
    path('songs/add/', songs_view.add_song, name='add_song'),
    path('songs/edit/<int:pk>/', songs_view.add_song, name='edit_song'),
    path('sets', sets_view.sets, name='sets'), 
    path('sets/stream-deck/', sets_view.stream_deck, name='stream_deck'),
    path('sets/add/', sets_view.add_set, name='add_set'),
    path('sets/edit/<int:pk>/', sets_view.add_set, name='edit_set'),
    path('sets/activate/<int:pk>/', sets_view.activate_set, name='activate_set'),
    path('sets/active/song/current/', sets_view.active_set_current_song, name='active_set_current_song'),
    path('sets/active/song/first/activate/', sets_view.active_set_activate_first, name='active_set_activate_first'),
    path('sets/active/song/last/activate/', sets_view.active_set_activate_last, name='active_set_activate_last'),
    path('sets/active/song/next/activate/', sets_view.active_set_activate_next, name='active_set_activate_next'),
    path('sets/active/song/prev/activate/', sets_view.active_set_activate_prev, name='active_set_activate_prev'),
    path('sets/active/song/metronome/start/', songs_view.metronome_start, name='metronome_start'),
    path('sets/active/song/metronome/stop/', songs_view.metronome_stop, name='metronome_stop'),
    path('sets/active/song/metronome/faster/', songs_view.metronome_faster, name='metronome_faster'),
    path('sets/active/song/metronome/slower/', songs_view.metronome_slower, name='metronome_slower'),
    path('sets/active/song/metronome/softer/', songs_view.metronome_softer, name='metronome_softer'),
    path('sets/active/song/metronome/louder/', songs_view.metronome_louder, name='metronome_louder'),
    path('sets/active/song/mp3/stop/', songs_view.stop_active_song_mp3, name='stop_active_song_mp3'),
    path('sets/active/song/pad/start/', sets_view.active_set_pad_start, name='active_set_pad_start'),
    path('sets/active/song/pad/stop/', sets_view.active_set_pad_stop, name='active_set_pad_stop'),
    path('pads/', pads_view.home, name='pads'),
    path('pad/add/', pads_view.add_pad, name='add_pad'),
    path('pad/edit/<int:pk>/', pads_view.add_pad, name='edit_pad'),
    path('pad/usage/<int:pk>/', pads_view.pad_usage, name='pad_usage'),
    path('pad/test/start/', pads_view.test_pad_start, name='test_pad_start'),
    path('pad/test/stop/', pads_view.test_pad_stop, name='test_pad_stop'),

]
