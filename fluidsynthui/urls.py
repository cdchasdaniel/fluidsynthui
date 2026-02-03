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
    path('sets/add/', sets_view.add_set, name='add_set'),
    path('sets/edit/<int:pk>/', sets_view.add_set, name='edit_set'),
    path('sets/activate/<int:pk>/', sets_view.activate_set, name='activate_set'),
    path('sets/active/song/<int:song_pk>/', sets_view.active_set_song_info, name='active_set_song_info'),
    path('sets/active/song/<int:song_pk>/prev/', sets_view.active_set_prev_song, name='active_set_prev_song'),
    path('sets/active/song/<int:song_pk>/next/', sets_view.active_set_next_song, name='active_set_next_song'),
    path('sets/active/songs/', sets_view.active_set_songs, name='active_set_songs'),
    path('sets/api/', sets_view.api_helper, name='sets_api_helper'),
    path('sets/active/song/next/activate/', sets_view.active_set_activate_next, name='active_set_activate_next'),
    path('sets/active/song/prev/activate/', sets_view.active_set_activate_prev, name='active_set_activate_prev'),

]
