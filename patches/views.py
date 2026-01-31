from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme

from bob import settings
from .models import Patch
from .forms import PatchForm, VoiceFormSet
from patches.synth.synth_manager import note_to_midi
import re
from .synth.soundfont import pull_out_preset


def patch_usage(request, pk):
    """Return JSON describing whether a Patch is referenced by any Song(s)."""
    patch = get_object_or_404(Patch, pk=pk)
    from songs.models import Song
    songs = list(Song.objects.filter(patch=patch).values('id', 'name'))
    return JsonResponse({'used': bool(songs), 'songs': songs})


def home(request):
    patches = Patch.objects.all()
    synth = getattr(settings, 'FLUID_SYNTH', None)
    active_id = synth.active_patch_id if synth else None
    return render(request, 'patches/patches.html', {
        'patches': patches,
        'active_patch_id': active_id
    })


def add_patch(request, pk=None):
    method = request.POST.get('_method', request.method).upper()
    instance = get_object_or_404(Patch, pk=pk) if pk else None
    form= None
    formset=None

    # 1. Capture the potential redirect target
    next_url = request.POST.get('next') or request.GET.get('next') or 'patches'
    print(next_url)

    # 2. Validate that next_url is a safe, internal path
    if not url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure()
    ):
        next_url = 'patches'  # Fallback to default if unsafe

    if method == "GET":
        form = PatchForm(instance=instance)
        formset = VoiceFormSet(instance=instance)
        return render(request, 'patches/add_patch.html', {
            'form': form,
            'formset': formset,
            'instance': instance,
            'next_url' : next_url
        })

    if method in ["PUT", "POST"]:
        form = PatchForm(request.POST, instance=instance)
        formset = VoiceFormSet(request.POST, instance=instance)

        if form.is_valid() and formset.is_valid():
            print("valid form")
            patch = form.save()
            # Ensure the formset knows the saved patch instance before creating related Voices
            formset.instance = patch
            voices = formset.save(commit=False)

            # Handle deletions (required when using commit=False)
            for obj in formset.deleted_objects:
                obj.delete()

            for voice in voices:
                # Pre-save normalization and preset parsing
                pull_out_preset(voice)
                voice.low_note = voice.low_note.strip().capitalize()
                voice.high_note = voice.high_note.strip().capitalize()
                # Ensure relation to the saved patch (defensive)
                voice.patch = patch
                print(f"preset name is {voice.preset_name}")
                voice.save()
            return redirect(next_url)
        else:
            print("invalid form")
            # 1. Capture Main Form Errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Patch {field}: {error}")

            # 2. Capture Formset (Voice) Errors
            for i, v_form in enumerate(formset):
                for field, errors in v_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Voice #{i + 1} {field}: {error}")

            # Handle non-form errors (e.g. management form corruption)
            for error in formset.non_form_errors():
                messages.error(request, error)

            # Return the same page so the user can fix the data
            return render(request, 'patches/add_patch.html', {
                'form': form, 'formset': formset, 'instance': instance
            })

    # Handle DELETE as before, but block deletion if any Song references this Patch
    if method == "DELETE" and instance:
        from songs.models import Song
        songs_using = Song.objects.filter(patch=instance)
        if songs_using.exists():
            names = ', '.join([s.name for s in songs_using])
            messages.error(request, f"Cannot delete patch '{instance.name}'; it is used by: {names}")
            return redirect('patches')
        instance.delete()
        messages.success(request, f"Deleted patch '{instance.name}'")
        return redirect('patches')

    print(f"next_url is {next_url}")
    return render(request, 'add_patch.html', {'form': form, 'formset': formset, 'next_url': next_url})


def apply_patch(request, pk):
    patch = get_object_or_404(Patch, pk=pk)
    synth_manager = getattr(settings, 'FLUID_SYNTH', None)

    if synth_manager:
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
        synth_manager.apply_patch(voices_data, patch.id, reverb_settings)
        print(f"Applied patch: {patch.name} to FluidSynth manager.")

    # Redirect back to the patches list page
    return redirect('patches')


def get_presets_json(request, sf_name):
    synth_manager = getattr(settings, 'FLUID_SYNTH', None)
    if sf_name:
        presets = synth_manager.all_soundfont_presets[sf_name]["presets"]
        return JsonResponse({'presets': presets})
    return JsonResponse({'presets': []}, status=400)



def apply_patch_preview(request):
    if request.method == 'POST':
        form = PatchForm(request.POST)
        formset = VoiceFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # 1. Gather Global Reverb from the main form cleaned_data
            reverb_data = {
                'room_size': form.cleaned_data.get('reverb_room_size', 0.5),
                'damping': form.cleaned_data.get('reverb_damping', 0.5),
                'width': form.cleaned_data.get('reverb_width', 0.5),
                'level': form.cleaned_data.get('reverb_level', 0.9),
            }
            voices_data = []

            for voice_dict in formset.cleaned_data:
                # Skip empty forms or those marked for deletion
                if not voice_dict or voice_dict.get('DELETE'):
                    continue

                full_string = voice_dict.get('preset', '')  # e.g. "Grand Piano 0:18"

                # --- APPLY YOUR REGEX LOGIC HERE ---
                match = re.search(r'^(.*?)\s*(\d+):(\d+)$', full_string)

                if match:
                    name_part, bank_str, num_str = match.groups()
                    # Add/Update keys in the dictionary for the hardware method
                    voice_dict['preset_name'] = name_part.strip()
                    voice_dict['preset'] = f"{int(bank_str):03d}:{int(num_str):03d}"
                else:
                    voice_dict['preset_name'] = full_string
                    voice_dict['preset'] = "000:000"

                # Standardize and Convert Notation to MIDI integers
                voice_dict['low_midi'] = note_to_midi(voice_dict.get('low_note', 'C0'))
                voice_dict['high_midi'] = note_to_midi(voice_dict.get('high_note', 'G10'))

                voices_data.append(voice_dict)

            # Now call the hardware with the enriched dictionary
            synth_manager = getattr(settings, 'FLUID_SYNTH', None)
            synth_manager.apply_patch(voices_data,
                                      None,
                                      reverb_data)

            return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)
