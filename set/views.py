from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from set.forms import SetForm
from .models import Set
from songs.models import Song
import json


def sets(request):
    # Order sets by performance date descending (newest first)
    sets = Set.objects.all().order_by('-date')
    return render(request, 'sets/sets.html', {
        'sets': sets,
    })


def activate_set(request, pk):
    """Mark the specified Set as active. Only accepts POST requests."""
    if request.method != 'POST':
        return redirect('sets')

    instance = get_object_or_404(Set, pk=pk)
    instance.active = True
    instance.save()
    messages.success(request, f"Set '{instance.name}' marked active.")
    return redirect('sets')


# --- Active-set JSON services ---
from django.http import JsonResponse
from django.db.models import F
from django.db import transaction


def _ensure_active_setsong(active):
    """Ensure exactly one SetSong in `active` is marked active. If none, activate the first ordered song."""
    from .models import SetSong
    if not SetSong.objects.filter(set=active, active=True).exists():
        ordered = _ordered_setsongs(active)
        if ordered:
            with transaction.atomic():
                SetSong.objects.filter(set=active).update(active=False)
                SetSong.objects.filter(pk=ordered[0].pk).update(active=True)


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


def active_set_song_info(request, song_pk):
    """Return JSON with song info plus per-set metadata for the active set."""
    active = _get_active_set()
    if not active:
        return JsonResponse({'error': 'No active set'}, status=404)

    song = get_object_or_404(Song, pk=song_pk)

    # Get set-specific metadata if present
    try:
        from .models import SetSong
        ss = SetSong.objects.filter(set=active, song=song).select_related('song').first()
    except Exception:
        ss = None

    data = {
        'song': {
            'id': song.pk,
            'name': song.name,
            'notes': song.notes,
            'tempo': song.tempo,
            'patch': {
                'id': song.patch.pk,
                'name': song.patch.name
            } if getattr(song, 'patch', None) else None,
        },
        'set': {
            'id': active.pk,
            'name': active.name,
            'date': active.date.isoformat() if active.date else None
        },
        'set_meta': {
            'order': ss.order if ss else None,
            'notes': ss.notes if ss else None,
        }
    }

    return JsonResponse(data)


def _ordered_setsongs(active):
    """Helper returning SetSong queryset ordered by order (nulls last)."""
    from .models import SetSong
    return list(SetSong.objects.filter(set=active).select_related('song').order_by(F('order').asc(nulls_last=True), 'song__name'))


def active_set_prev_song(request, song_pk):
    """Return name and pk of the previous song in the active set (or null)."""
    active = _get_active_set()
    if not active:
        return JsonResponse({'error': 'No active set'}, status=404)

    ordered = _ordered_setsongs(active)
    idx = next((i for i, ss in enumerate(ordered) if ss.song_id == song_pk), None)
    if idx is None:
        return JsonResponse({'error': 'Song not in active set'}, status=404)

    prev_item = ordered[idx - 1] if idx > 0 else None
    if not prev_item:
        return JsonResponse({'song': None})

    return JsonResponse({'song': {'id': prev_item.song.pk, 'name': prev_item.song.name}})


def active_set_next_song(request, song_pk):
    """Return name and pk of the next song in the active set (or null)."""
    active = _get_active_set()
    if not active:
        return JsonResponse({'error': 'No active set'}, status=404)

    ordered = _ordered_setsongs(active)
    idx = next((i for i, ss in enumerate(ordered) if ss.song_id == song_pk), None)
    if idx is None:
        return JsonResponse({'error': 'Song not in active set'}, status=404)

    next_item = ordered[idx + 1] if idx < len(ordered) - 1 else None
    if not next_item:
        return JsonResponse({'song': None})

    return JsonResponse({'song': {'id': next_item.song.pk, 'name': next_item.song.name}})


from django.db import transaction


def active_set_activate_next(request):
    """Mark the next song in the active set as active (POST only)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

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
        return JsonResponse({'song': None})

    target = ordered[target_idx]
    with transaction.atomic():
        # Deactivate all then activate target
        from .models import SetSong
        SetSong.objects.filter(set=active).update(active=False)
        SetSong.objects.filter(pk=target.pk).update(active=True)

    return JsonResponse({'song': {'id': target.song.pk, 'name': target.song.name}})


def active_set_activate_prev(request):
    """Mark the previous song in the active set as active (POST only)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

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
        return JsonResponse({'song': None})

    target = ordered[target_idx]
    with transaction.atomic():
        from .models import SetSong
        SetSong.objects.filter(set=active).update(active=False)
        SetSong.objects.filter(pk=target.pk).update(active=True)

    return JsonResponse({'song': {'id': target.song.pk, 'name': target.song.name}})


def active_set_songs(request):
    """Return the ordered list of songs (id, name, order, active) for the active set."""
    active = _get_active_set()
    if not active:
        return JsonResponse({'error': 'No active set'}, status=404)

    # Get fresh queryset to ensure active status is current
    ordered = _ordered_setsongs(active)
    
    songs = [
        {'id': ss.song.pk, 'name': ss.song.name, 'order': ss.order, 'active': ss.active}
        for ss in ordered
    ]

    return JsonResponse({'songs': songs})


def api_helper(request):
    """Render a small helper page so users can call the JSON services from a browser."""
    return render(request, 'sets/api_helper.html')

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