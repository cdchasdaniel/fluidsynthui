from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings

from songs.forms import SongForm
from songs.models import Song
from patches.models import Patch
from django.contrib import messages


def home(request):
    # Always present songs ordered by title for predictable listing
    songs = Song.objects.all().order_by('name')
    synth = getattr(settings, 'FLUID_SYNTH', None)
    active_id = synth.active_patch_id if synth else None
    return render(request, 'songs/songs.html', {
        'songs': songs
    })



def add_song(request, pk=None):
    method = request.POST.get('_method', request.method).upper()
    instance = get_object_or_404(Song, pk=pk) if pk else None

    # Handle DELETE override (from the list 'delete' form)
    if method == "DELETE" and instance:
        instance.delete()
        return redirect('songs')

    if method in ["POST", "PUT"]:
        # Bind the form with POST data and the instance (if editing)
        form = SongForm(request.POST, instance=instance)

        # Ensure the 'patch' field queryset includes the submitted patch value
        # before validation so Django won't reject it as "not a valid choice.".
        try:
            selected_patch_id = request.POST.get('patch')
            assigned_patch_ids = Song.objects.values_list('patch_id', flat=True)
            qs = Patch.objects.exclude(id__in=assigned_patch_ids)
            # Include the selected patch even if it's assigned or otherwise excluded
            if selected_patch_id:
                try:
                    sel = Patch.objects.filter(id=int(selected_patch_id))
                    qs = sel | qs
                except ValueError:
                    pass
            if not qs.exists():
                qs = Patch.objects.all()
            form.fields['patch'].queryset = qs
        except Exception:
            form.fields['patch'].queryset = Patch.objects.all()

        if form.is_valid():
            form.save()
            messages.success(request, "Song saved")
            # Redirect to your songs list view after a successful save
            return redirect('songs')
        else:
            # Provide user-visible error messages to make validation failures clear
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

            # Ensure the 'patch' queryset remains populated for re-render
            try:
                if not form.fields['patch'].queryset.exists():
                    form.fields['patch'].queryset = Patch.objects.all()
            except Exception:
                form.fields['patch'].queryset = Patch.objects.all()
    else:
        # GET request: Instantiate an empty or pre-filled form
        form = SongForm(instance=instance)
        # Ensure the patch queryset is populated (show unassigned patches on add)
        try:
            if not instance:
                assigned_patch_ids = Song.objects.values_list('patch_id', flat=True)
                qs = Patch.objects.exclude(id__in=assigned_patch_ids)
                # If none available (all patches assigned), fall back to showing all patches
                if not qs.exists():
                    qs = Patch.objects.all()
                form.fields['patch'].queryset = qs
        except Exception:
            # Defensive: fallback to showing all patches
            form.fields['patch'].queryset = Patch.objects.all()

    context = {
        'form': form,
        'instance': instance,  # Used by the template to toggle "Edit" vs "New" headings
    }
    return render(request, 'songs/add_songs.html', context)


def metronome_start(request):
    """Start the metronome using the current active song's tempo and time signature"""
    try:
        from set.models import Set, SetSong
        
        # Get the active set and its active song
        active_set = Set.objects.filter(active=True).first()
        if not active_set:
            return JsonResponse({
                'success': False,
                'error': 'No active set'
            }, status=400)
        
        active_song_entry = SetSong.objects.filter(set=active_set, active=True).first()
        if not active_song_entry:
            return JsonResponse({
                'success': False,
                'error': 'No active song in the active set'
            }, status=400)
        
        song = active_song_entry.song
        # Use song's tempo if available, otherwise default to 100
        bpm = song.tempo if song.tempo else 100
        
        # Parse time signature (e.g., "4/4" or "6/8")
        time_sig = song.time_signature if song.time_signature else "4/4"
        beats_per_measure, note_value = map(int, time_sig.split('/'))
        
        metronome = settings.METRONOME_MANAGER
        if not metronome:
            return JsonResponse({
                'success': False,
                'error': 'Metronome not available - manager is None'
            }, status=500)
        
        # Stop any currently running metronome first
        metronome.stop()
        
        # Start the new metronome with cowbell on beat 1 (MIDI note 102 = bright cowbell)
        metronome.start(bpm=bpm, beats_per_measure=beats_per_measure, 
                       note_value=note_value, cowbell_note=102)
        return JsonResponse({
            'success': True,
            'bpm': str(bpm),
            'time_signature': time_sig,
            'song': song.name
        })
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


def metronome_stop(request):
    """Stop the metronome"""
    try:
        metronome = getattr(settings, 'METRONOME_MANAGER', None)
        if not metronome:
            return JsonResponse({
                'success': False,
                'error': 'Metronome not available - manager is None'
            }, status=500)
        
        metronome.stop()
        return JsonResponse({'success': True})
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


def metronome_faster(request):
    """Increase metronome BPM by 1"""
    try:
        metronome = getattr(settings, 'METRONOME_MANAGER', None)
        if not metronome:
            return JsonResponse({
                'success': False,
                'error': 'Metronome not available - manager is None'
            }, status=500)
        
        # Get current config and increase BPM by 1
        if not metronome.is_running:
            return JsonResponse({
                'success': False,
                'error': 'Metronome not running'
            }, status=400)
        
        current_bpm = metronome.current_config.get('bpm', 100) if metronome.current_config else 100
        new_bpm = current_bpm + 1
        
        # Set the new BPM
        metronome.set_bpm(new_bpm)
        
        return JsonResponse({
            'success': True,
            'bpm': new_bpm,
            'song': '(metronome running)'
        })
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


def metronome_slower(request):
    """Decrease metronome BPM by 1"""
    try:
        metronome = getattr(settings, 'METRONOME_MANAGER', None)
        if not metronome:
            return JsonResponse({
                'success': False,
                'error': 'Metronome not available - manager is None'
            }, status=500)
        
        # Get current config and decrease BPM by 1
        if not metronome.is_running:
            return JsonResponse({
                'success': False,
                'error': 'Metronome not running'
            }, status=400)
        
        current_bpm = metronome.current_config.get('bpm', 100) if metronome.current_config else 100
        new_bpm = max(1, current_bpm - 1)  # Ensure BPM doesn't go below 1
        
        # Set the new BPM
        metronome.set_bpm(new_bpm)
        
        return JsonResponse({
            'success': True,
            'bpm': new_bpm,
            'song': '(metronome running)'
        })
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


def metronome_softer(request):
    """Decrease metronome gain by 0.1"""
    try:
        metronome = getattr(settings, 'METRONOME_MANAGER', None)
        if not metronome:
            return JsonResponse({
                'success': False,
                'error': 'Metronome not available - manager is None'
            }, status=500)
        
        # Get current gain and decrease by 0.1
        current_gain = metronome.current_gain if hasattr(metronome, 'current_gain') else 5.0
        new_gain = max(0.0, current_gain - 0.1)  # Ensure gain doesn't go below 0
        new_gain = round(new_gain, 1)  # Round to 1 decimal place
        
        # Set the new gain
        metronome.set_gain(new_gain)
        
        return JsonResponse({
            'success': True,
            'gain': new_gain,
            'message': 'Metronome volume decreased'
        })
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


def metronome_louder(request):
    """Increase metronome gain by 0.1"""
    try:
        metronome = getattr(settings, 'METRONOME_MANAGER', None)
        if not metronome:
            return JsonResponse({
                'success': False,
                'error': 'Metronome not available - manager is None'
            }, status=500)
        
        # Get current gain and increase by 0.1
        current_gain = metronome.current_gain if hasattr(metronome, 'current_gain') else 5.0
        new_gain = min(5.0, current_gain + 0.1)  # Ensure gain doesn't exceed 5.0
        new_gain = round(new_gain, 1)  # Round to 1 decimal place
        
        # Set the new gain
        metronome.set_gain(new_gain)
        
        return JsonResponse({
            'success': True,
            'gain': str(new_gain),
            'message': 'Metronome volume increased'
        })
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)



