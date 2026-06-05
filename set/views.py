from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from set.forms import SetForm
from .models import Set
from songs.models import Song
from patches.models import Patch
import json
# --- Active-set JSON services ---
from django.http import JsonResponse
from django.db.models import F
from django.db import transaction
from django.conf import settings

def sets(request):
    # Order sets by performance date descending (newest first)
    sets = Set.objects.all().order_by('-date')
    active = _get_active_set()
    active_song = None
    if active:
        from .models import SetSong
        active_song = SetSong.objects.filter(set=active, active=True).select_related('song').first()
    return render(request, 'sets/sets.html', {
        'sets': sets,
        'active_song': active_song,
    })


def activate_set(request, pk):
    """Mark the specified Set as active. Only accepts POST requests."""
    if request.method != 'POST':
        return redirect('sets')

    instance = get_object_or_404(Set, pk=pk)
    instance.active = True
    instance.save()
    ordered = _ordered_setsongs(instance)
    if ordered:
        with transaction.atomic():
            from .models import SetSong
            SetSong.objects.filter(set=instance).update(active=False)
            SetSong.objects.filter(pk=ordered[0].pk).update(active=True)
        _apply_song_patch_if_any(ordered[0].song)
    messages.success(request, f"Set '{instance.name}' marked active.")
    return redirect('sets')



def _ensure_active_setsong(active):
    """Ensure exactly one SetSong in `active` is marked active. If none, activate the first ordered song."""
    from .models import SetSong
    if not SetSong.objects.filter(set=active, active=True).exists():
        ordered = _ordered_setsongs(active)
        if ordered:
            with transaction.atomic():
                SetSong.objects.filter(set=active).update(active=False)
                SetSong.objects.filter(pk=ordered[0].pk).update(active=True)
            _apply_song_patch_if_any(ordered[0].song)


def _apply_song_patch_if_any(song):
    """Apply the patch associated with a Song, if one exists."""
    synth = getattr(settings, 'FLUID_SYNTH', None)
    if not synth:
        print("No synth manager available")
        return

    patch = getattr(song, 'patch', None)
    if not patch:
        # Try to use the Standard Piano patch as default
        standard_piano = Patch.objects.filter(name='Standard Piano').first()
        if standard_piano:
            patch = standard_piano
        else:
            # Fallback to hardcoded default if Standard Piano doesn't exist
            default_voice = {
                'channel': 1,
                'file_name': 'defaultGM.sf2',
                'preset': '000:000',
                'sustain': False,
                'volume': 100,
                'transpose': 0,
                'low_note': 'C0',
                'high_note': 'G10',
            }
            synth.apply_patch(
                [default_voice],
                None,
                {
                    'room_size': 0.5,
                    'damping': 0.5,
                    'width': 0.5,
                    'level': 0.9,
                },
            )
            if hasattr(synth, 'apply_song_mp3_slots'):
                synth.apply_song_mp3_slots(song)
            return

    voices_data = list(patch.voices.all().values(
        'channel', 'file_name', 'preset', 'sustain',
        'volume', 'transpose', 'low_note', 'high_note'
    ))
    reverb_settings = {
        'room_size': patch.reverb_room_size,
        'damping': patch.reverb_damping,
        'width': patch.reverb_width,
        'level': patch.reverb_level,
    }
    print(f"Applying patch for song {song.name}")
    synth.apply_patch(voices_data, patch.id, reverb_settings)
    if hasattr(synth, 'apply_song_mp3_slots'):
        synth.apply_song_mp3_slots(song)


def _get_active_set():
    # Return the active set; if none exists, default to the most recent by date and make it active.
    active = Set.objects.filter(active=True).first()
    if not active:
        latest = Set.objects.order_by('-date').first()
        if latest:
            latest.active = True
            latest.save()
            _ensure_active_setsong(latest)
            return latest
        return None

    # Make sure an active songs exists for the active set
    _ensure_active_setsong(active)
    return active


def _ordered_setsongs(active):
    """Helper returning SetSong queryset ordered by order (nulls last)."""
    from .models import SetSong
    return list(SetSong.objects.filter(set=active).select_related('song').order_by(F('order').asc(nulls_last=True), 'song__name'))

def active_set_activate_next(request):
    """Mark the next song in the active set as active (POST or GET)."""
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'POST or GET required'}, status=405)

    # Stop metronome when changing songs
    metronome = getattr(settings, 'METRONOME_MANAGER', None)
    if metronome:
        metronome.stop()

    active = _get_active_set()
    if not active:
        return JsonResponse({'error': 'No active set'}, status=404)

    ordered = _ordered_setsongs(active)
    if not ordered:
        return JsonResponse({'error': 'Active set has no songs'}, status=400)

    # Find current index (by SetSong.active). If none, start at 0
    current_idx = next((i for i, ss in enumerate(ordered) if ss.active), None)
    if current_idx is None:
        target_idx = 0
    else:
        target_idx = current_idx + 1

    if target_idx >= len(ordered):
        return JsonResponse({'song': None, 'current_song_name': None})

    target = ordered[target_idx]
    with transaction.atomic():
        # Deactivate all then activate target
        from .models import SetSong
        SetSong.objects.filter(set=active).update(active=False)
        SetSong.objects.filter(pk=target.pk).update(active=True)

    _apply_song_patch_if_any(target.song)

    return JsonResponse({
        'song': {'id': target.song.pk, 'name': target.song.name},
        'current_song_name': target.song.name,
    })


def active_set_activate_prev(request):
    """Mark the previous song in the active set as active (POST or GET)."""
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'POST or GET required'}, status=405)

    # Stop metronome when changing songs
    metronome = getattr(settings, 'METRONOME_MANAGER', None)
    if metronome:
        metronome.stop()

    active = _get_active_set()
    if not active:
        return JsonResponse({'error': 'No active set'}, status=404)

    ordered = _ordered_setsongs(active)
    if not ordered:
        return JsonResponse({'error': 'Active set has no songs'}, status=400)

    current_idx = next((i for i, ss in enumerate(ordered) if ss.active), None)
    if current_idx is None:
        target_idx = len(ordered) - 1
    else:
        target_idx = current_idx - 1

    if target_idx < 0:
        return JsonResponse({'song': None, 'current_song_name': None})

    target = ordered[target_idx]
    with transaction.atomic():
        from .models import SetSong
        SetSong.objects.filter(set=active).update(active=False)
        SetSong.objects.filter(pk=target.pk).update(active=True)

    _apply_song_patch_if_any(target.song)

    return JsonResponse({
        'song': {'id': target.song.pk, 'name': target.song.name},
        'current_song_name': target.song.name,
    })


def active_set_activate_first(request):
    """Mark the first song in the active set as active (POST or GET)."""
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'POST or GET required'}, status=405)

    # Stop metronome when changing songs
    metronome = getattr(settings, 'METRONOME_MANAGER', None)
    if metronome:
        metronome.stop()

    active = _get_active_set()
    if not active:
        return JsonResponse({'error': 'No active set'}, status=404)

    ordered = _ordered_setsongs(active)
    if not ordered:
        return JsonResponse({'error': 'Active set has no songs'}, status=400)

    target = ordered[0]
    with transaction.atomic():
        from .models import SetSong
        SetSong.objects.filter(set=active).update(active=False)
        SetSong.objects.filter(pk=target.pk).update(active=True)

    _apply_song_patch_if_any(target.song)

    return JsonResponse({
        'song': {'id': target.song.pk, 'name': target.song.name},
        'current_song_name': target.song.name,
    })


def active_set_activate_last(request):
    """Mark the last song in the active set as active (POST or GET)."""
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'POST or GET required'}, status=405)

    # Stop metronome when changing songs
    metronome = getattr(settings, 'METRONOME_MANAGER', None)
    if metronome:
        metronome.stop()

    active = _get_active_set()
    if not active:
        return JsonResponse({'error': 'No active set'}, status=404)

    ordered = _ordered_setsongs(active)
    if not ordered:
        return JsonResponse({'error': 'Active set has no songs'}, status=400)

    target = ordered[-1]
    with transaction.atomic():
        from .models import SetSong
        SetSong.objects.filter(set=active).update(active=False)
        SetSong.objects.filter(pk=target.pk).update(active=True)

    _apply_song_patch_if_any(target.song)

    return JsonResponse({
        'song': {'id': target.song.pk, 'name': target.song.name},
        'current_song_name': target.song.name,
    })


def active_set_current_song(request):
    """Return the currently active song for the active set (or null)."""
    active = Set.objects.filter(active=True).first()
    if not active:
        return JsonResponse({'error': 'No active set'}, status=404)

    from .models import SetSong
    ss = SetSong.objects.filter(set=active, active=True).select_related('song').first()
    if not ss:
        return JsonResponse({'song': None})
    json = {
        'current_song_name': ss.song.name,
        'current_song_id': ss.song.id
    }
    return JsonResponse(json)


def add_set(request, pk=None):
    method = request.POST.get('_method', request.method).upper()
    instance = get_object_or_404(Set, pk=pk) if pk else None
    form = None

    if method == "GET":
        form = SetForm(instance=instance)
        songs = Song.objects.order_by('name').values('id', 'name')
        songs_json = json.dumps(list(songs))
        if instance:
            # load per-song metadata from the through model
            songs_meta = list(instance.setsong_set.select_related('song').values('song_id', 'order', 'notes', 'song__name'))
            songs_meta_json = json.dumps(songs_meta)
            selected_ids = [m['song_id'] for m in songs_meta]
        else:
            songs_meta_json = json.dumps([])
            selected_ids = []
        return render(request, 'sets/add_set.html', {
            'form': form,
            'instance': instance,
            'songs_json': songs_json,
            'selected_ids': selected_ids,
            'songs_meta_json': songs_meta_json,
        })

    if method in ["PUT", "POST"]:
        form = SetForm(request.POST, instance=instance)

        if form.is_valid():
            set_obj = form.save()

            # Process per-song metadata sent as JSON in 'set_songs'
            set_songs_raw = request.POST.get('set_songs')
            if set_songs_raw:
                try:
                    songs_meta = json.loads(set_songs_raw)
                except Exception:
                    songs_meta = []

                # Track incoming song IDs
                incoming_ids = []
                for item in songs_meta:
                    song_id = int(item.get('id'))
                    incoming_ids.append(song_id)
                    order = item.get('order')
                    try:
                        order = int(order)
                    except Exception:
                        order = None
                    notes = item.get('notes') if item.get('notes') is not None else ''

                    from .models import SetSong
                    SetSong.objects.update_or_create(set=set_obj, song_id=song_id, defaults={'order': order, 'notes': notes})

                # Remove SetSong entries that are no longer included
                from .models import SetSong
                SetSong.objects.filter(set=set_obj).exclude(song_id__in=incoming_ids).delete()

            messages.success(request, f"Set {'updated' if instance else 'created'} successfully.")
            return redirect('sets')
        else:
            print("invalid form")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Set {field}: {error}")

            # Return the same page so the user can fix the data
            songs = Song.objects.order_by('name').values('id', 'name')
            songs_json = json.dumps(list(songs))
            # If the user submitted set_songs, use that to repopulate the editor
            set_songs_raw = request.POST.get('set_songs')
            if set_songs_raw:
                try:
                    songs_meta = json.loads(set_songs_raw)
                    songs_meta_json = json.dumps(songs_meta)
                    selected_ids = [int(item['id']) for item in songs_meta]
                except Exception:
                    songs_meta_json = json.dumps([])
                    selected_ids = []
            else:
                songs_meta_json = json.dumps([])
                selected_ids = list(instance.songs.values_list('id', flat=True)) if instance else []

            return render(request, 'sets/add_set.html', {
                'form': form, 'instance': instance,
                'songs_json': songs_json,
                'selected_ids': selected_ids,
                'songs_meta_json': songs_meta_json,
            })

    # Handle DELETE as before
    if method == "DELETE" and instance:
        instance.delete()
        messages.success(request, "Set deleted")
        return redirect('sets')

    return render(request, 'sets/add_set.html', {'form': form})


def stream_deck(request):
    """Stream deck view with Prev and Next buttons."""
    active = _get_active_set()
    if not active:
        return render(request, 'sets/stream_deck.html', {
            'current_song': None,
        })
    
    ordered = _ordered_setsongs(active)
    if not ordered:
        return render(request, 'sets/stream_deck.html', {
            'current_song': None,
        })
    
    # Find current song
    current_idx = next((i for i, ss in enumerate(ordered) if ss.active), None)
    if current_idx is None:
        current_idx = 0
    
    current_song = ordered[current_idx].song.name if current_idx < len(ordered) else None
    
    return render(request, 'sets/stream_deck.html', {
        'current_song': current_song,
    })


def active_set_pad_start(request):
    """Start playing the pad for the active song (POST or GET)."""
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'POST or GET required'}, status=405)

    try:
        active = _get_active_set()
        if not active:
            return JsonResponse({'success': False, 'error': 'No active set'}, status=404)

        from .models import SetSong
        ss = SetSong.objects.filter(set=active, active=True).select_related('song').first()
        if not ss:
            return JsonResponse({'success': False, 'error': 'No active song'}, status=404)

        song = ss.song
        pad = song.pad
        if not pad:
            return JsonResponse({
                'success': False,
                'error': 'No pad configured for this song'
            }, status=400)

        # Start pad using PadManager
        pad_manager = getattr(settings, 'PAD_MANAGER', None)
        if not pad_manager:
            return JsonResponse({
                'success': False,
                'error': 'Pad manager not available'
            }, status=500)

        if pad_manager.start_pad(pad):
            return JsonResponse({
                'success': True,
                'pad_name': pad.name,
                'song_name': song.name,
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to start pad'
            }, status=500)

    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


def active_set_pad_stop(request):
    """Stop playing the pad (POST or GET)."""
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'POST or GET required'}, status=405)

    try:
        pad_manager = getattr(settings, 'PAD_MANAGER', None)
        if not pad_manager:
            return JsonResponse({
                'success': False,
                'error': 'Pad manager not available'
            }, status=500)

        if pad_manager.stop_pad():
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to stop pad'
            }, status=500)

    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


def active_set_pad_toggle(request):
    """Toggle pad playback for the active song (start if stopped, stop if playing)."""
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'POST or GET required'}, status=405)

    try:
        pad_manager = getattr(settings, 'PAD_MANAGER', None)
        if not pad_manager:
            return JsonResponse({
                'success': False,
                'error': 'Pad manager not available'
            }, status=500)

        # Check if pad is currently playing
        is_playing = pad_manager.is_pad_playing()

        if is_playing:
            # Stop the pad
            if pad_manager.stop_pad():
                return JsonResponse({
                    'success': True,
                    'action': 'stopped',
                    'is_playing': False
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to stop pad'
                }, status=500)
        else:
            # Start the pad
            try:
                active = _get_active_set()
                if not active:
                    return JsonResponse({'success': False, 'error': 'No active set'}, status=404)

                from .models import SetSong
                ss = SetSong.objects.filter(set=active, active=True).select_related('song').first()
                if not ss:
                    return JsonResponse({'success': False, 'error': 'No active song'}, status=404)

                song = ss.song
                pad = song.pad
                if not pad:
                    return JsonResponse({
                        'success': False,
                        'error': 'No pad configured for this song'
                    }, status=400)

                if pad_manager.start_pad(pad):
                    return JsonResponse({
                        'success': True,
                        'action': 'started',
                        'is_playing': True,
                        'pad_name': pad.name,
                        'song_name': song.name,
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Failed to start pad'
                    }, status=500)

            except Exception as e:
                import traceback
                return JsonResponse({
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }, status=500)

    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)