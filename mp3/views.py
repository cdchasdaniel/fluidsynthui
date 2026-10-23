from pathlib import Path

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from patches.synth import play_mp3_file, stop_mp3_playback
from set.models import Set, SetSong
from .utils import find_song_references, get_max_upload_mb, get_mp3_directory


def library(request):
    directory = get_mp3_directory()
    files = []
    for path in sorted(directory.iterdir(), key=lambda item: item.name.casefold()):
        if not path.is_file() or path.suffix.lower() != '.mp3':
            continue
        files.append({
            'name': path.name,
            'size': path.stat().st_size,
            'songs': find_song_references(path.name),
        })
    return render(request, 'mp3/library.html', {
        'files': files,
        'max_upload_mb': get_max_upload_mb(),
    })


@require_POST
def upload(request):
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        messages.error(request, 'Choose an MP3 file to upload.')
        return redirect('mp3_library')

    filename = Path(uploaded_file.name.replace('\\', '/')).name
    if not filename or filename in {'.', '..'} or Path(filename).suffix.lower() != '.mp3':
        messages.error(request, 'Only .mp3 files can be uploaded.')
        return redirect('mp3_library')

    max_upload_mb = get_max_upload_mb()
    if uploaded_file.size > max_upload_mb * 1024 * 1024:
        messages.error(request, f'File exceeds the {max_upload_mb} MB upload limit.')
        return redirect('mp3_library')

    directory = get_mp3_directory()
    if any(path.name.casefold() == filename.casefold() for path in directory.iterdir()):
        messages.error(request, f'A file named "{filename}" already exists.')
        return redirect('mp3_library')

    destination = directory / filename
    try:
        with destination.open('xb') as output:
            for chunk in uploaded_file.chunks():
                output.write(chunk)
    except FileExistsError:
        messages.error(request, f'A file named "{filename}" already exists.')
        return redirect('mp3_library')

    messages.success(request, f'Uploaded "{filename}".')
    return redirect('mp3_library')


@require_POST
def delete(request):
    filename = request.POST.get('filename', '')
    if not filename or Path(filename).name != filename:
        messages.error(request, 'Invalid MP3 filename.')
        return redirect('mp3_library')

    directory = get_mp3_directory()
    path = directory / filename
    if not path.is_file() or path.suffix.lower() != '.mp3':
        messages.error(request, 'MP3 file not found.')
        return redirect('mp3_library')

    songs_using_file = find_song_references(filename)
    if songs_using_file:
        song_names = ', '.join(song.name for song in songs_using_file)
        messages.error(request, f'Cannot delete "{filename}"; it is used by: {song_names}.')
        return redirect('mp3_library')

    path.unlink()
    messages.success(request, f'Deleted "{filename}".')
    return redirect('mp3_library')


@csrf_exempt
@require_POST
def play_slot(request, slot):
    if slot < 1 or slot > 8:
        return JsonResponse({'success': False, 'error': 'Slot must be between 1 and 8.'}, status=400)

    active_set = Set.objects.filter(active=True).first()
    if not active_set:
        return JsonResponse({'success': False, 'error': 'No active set.'}, status=404)

    active_entry = SetSong.objects.filter(
        set=active_set,
        active=True,
    ).select_related('song').first()
    if not active_entry:
        return JsonResponse({'success': False, 'error': 'No active song.'}, status=404)

    song = active_entry.song
    filename = getattr(song, f'mp3_slot_{slot}', None)
    if not filename:
        return JsonResponse({
            'success': False,
            'error': f'Button {slot} has no MP3 assigned for {song.name}.',
        }, status=404)

    directory = get_mp3_directory()
    if Path(filename).name != filename or Path(filename).suffix.lower() != '.mp3':
        return JsonResponse({'success': False, 'error': 'Invalid MP3 filename.'}, status=400)
    path = directory / filename
    if not path.is_file():
        return JsonResponse({'success': False, 'error': f'MP3 file not found: {filename}.'}, status=404)

    try:
        if stop_mp3_playback(-1) != 0:
            raise RuntimeError('Could not stop existing MP3 playback.')
        if play_mp3_file(str(path).encode('utf-8'), slot - 1) != 0:
            raise RuntimeError('Could not start MP3 playback.')
        return JsonResponse({
            'success': True,
            'slot': slot,
            'song': song.name,
            'file': filename,
        })
    except Exception as error:
        return JsonResponse({'success': False, 'error': str(error)}, status=500)


@csrf_exempt
@require_POST
def stop(request):
    try:
        if stop_mp3_playback(-1) != 0:
            raise RuntimeError('Could not stop MP3 playback.')
        return JsonResponse({'success': True})
    except Exception as error:
        return JsonResponse({'success': False, 'error': str(error)}, status=500)