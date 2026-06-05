from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from fluidsynthui import settings
from .models import Pad
from .forms import PadForm


def home(request):
    """List all pads."""
    pads = Pad.objects.all().order_by('name')
    return render(request, 'pads/pads.html', {'pads': pads})


def add_pad(request, pk=None):
    """Add or edit a pad."""
    method = request.POST.get('_method', request.method).upper()
    instance = get_object_or_404(Pad, pk=pk) if pk else None

    if method == "GET":
        form = PadForm(instance=instance)
        return render(request, 'pads/add_pad.html', {
            'form': form,
            'instance': instance,
        })

    if method in ["PUT", "POST"]:
        form = PadForm(request.POST, instance=instance)
        if form.is_valid():
            pad = form.save()
            messages.success(request, f"Pad '{pad.name}' saved successfully")
            return redirect('pads')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return render(request, 'pads/add_pad.html', {
                'form': form,
                'instance': instance,
            })

    if method == "DELETE" and instance:
        from songs.models import Song
        songs_using = Song.objects.filter(pad=instance)
        if songs_using.exists():
            names = ', '.join([s.name for s in songs_using])
            messages.error(request, f"Cannot delete pad '{instance.name}'; it is used by: {names}")
            return redirect('pads')
        instance.delete()
        messages.success(request, f"Deleted pad '{instance.name}'")
        return redirect('pads')

    return render(request, 'pads/add_pad.html', {'form': form, 'instance': instance})


def pad_usage(request, pk):
    """Return JSON describing whether a Pad is referenced by any Song(s)."""
    pad = get_object_or_404(Pad, pk=pk)
    from songs.models import Song
    songs = list(Song.objects.filter(pad=pad).values('id', 'name'))
    return JsonResponse({'used': bool(songs), 'songs': songs})


def test_pad_start(request):
    """Start playing a pad for testing purposes."""
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        # Import settings directly to ensure fresh reference
        from django.conf import settings as django_settings
        pad_manager = getattr(django_settings, 'PAD_MANAGER', None)
        print(f"[TEST] PAD_MANAGER from settings: {pad_manager}")
        print(f"[TEST] Is None? {pad_manager is None}")
        
        if pad_manager is None:
            return JsonResponse({'success': False, 'error': 'Pad manager not found in settings'}, status=500)
        
        print(f"[TEST] PAD_MANAGER.initialized: {pad_manager.initialized}")
        if not pad_manager.initialized:
            return JsonResponse({'success': False, 'error': 'Pad manager not initialized - check server logs'}, status=500)
        
        # Get form data
        file_name = request.POST.get('file_name') or request.GET.get('file_name')
        preset = request.POST.get('preset') or request.GET.get('preset')
        notes_str = request.POST.get('notes') or request.GET.get('notes')
        velocity = int(request.POST.get('velocity', 100) or request.GET.get('velocity', 100))
        fade_in_duration = float(request.POST.get('fade_in_duration', 0) or request.GET.get('fade_in_duration', 0))
        
        # Parse notes
        try:
            note_strs = [n.strip() for n in notes_str.split(',') if n.strip()]
            from patches.utils import note_to_midi
            notes = [note_to_midi(n) for n in note_strs]
        except (ValueError, TypeError):
            notes = [60]
        
        # Parse preset (bank:program)
        try:
            bank, program = preset.split(':')
            bank, program = int(bank.strip()), int(program.strip())
        except (ValueError, AttributeError):
            bank, program = 0, 0
        
        # Create a temporary Pad object with the test configuration
        test_pad = Pad(
            name='test',
            file_name=file_name,
            preset=f'{bank}:{program}',
            preset_name='Test Preset',
            velocity=velocity,
            fade_in_duration=fade_in_duration,
            notes_json=str(notes)
        )
        
        # Start the pad
        pad_manager.start_pad(test_pad)
        return JsonResponse({'success': True, 'message': f'Pad started with {len(notes)} notes'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def test_pad_stop(request):
    """Stop playing the test pad."""
    try:
        from django.conf import settings as django_settings
        pad_manager = getattr(django_settings, 'PAD_MANAGER', None)
        if not pad_manager:
            return JsonResponse({'success': False, 'error': 'Pad manager not initialized'}, status=500)
        
        pad_manager.stop_pad()
        return JsonResponse({'success': True, 'message': 'Pad stopped'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
