from django.shortcuts import render, get_object_or_404, redirect

from fluidsynthui import settings
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

