from django.shortcuts import render

from set.models import Set, SetSong


def home(request):
    active_set = Set.objects.filter(active=True).first()
    active_entry = None
    if active_set:
        active_entry = SetSong.objects.filter(
            set=active_set,
            active=True,
        ).select_related('song').first()
        if not active_entry:
            active_entry = SetSong.objects.filter(
                set=active_set,
            ).select_related('song').first()
    current_song = active_entry.song if active_entry else None

    slots = [
        {
            'number': slot,
            'filename': getattr(current_song, f'mp3_slot_{slot}', None) if current_song else None,
        }
        for slot in range(1, 9)
    ]
    return render(request, 'streamdeck/stream_deck.html', {
        'current_song': current_song.name if current_song else None,
        'mp3_slots': slots,
    })