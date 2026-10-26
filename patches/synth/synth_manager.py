import atexit
import logging
import os
from django.conf import settings
from django.db import transaction
from django.db.models import F
from set.models import Set, SetSong
from patches.models import Patch
from . import init_midi_device, cleanup_midi_device, set_channel_preset, route_notes_to_channel, route_sustain_to_channel, set_reverb, get_soundfont_by_name, clear_router
from ..utils import note_to_midi

logger = logging.getLogger(__name__)


class FluidMidiManager:
    def __init__(self):
        # Initialize Synth with config file path
        config_path = os.path.join(settings.BASE_DIR, 'fluidsynth.cfg')
        self.fs = init_midi_device(config_path.encode('utf-8'))
        self.active_patch_id = None
        self._activate_first_song_in_active_set()
        atexit.register(self.cleanup)


    def apply_patch(self, voices_data, patch_id, reverb_settings):
        if patch_id:
            self.active_patch_id = patch_id
        clear_router()
        self.apply_reverb(reverb_settings)
        
        for voice in voices_data:
            channel = voice["channel"] - 1
            print(f"DEBUG: set_channel_preset(channel={channel}, file={voice['file_name']}, preset={voice['preset']})")
            set_channel_preset(channel, voice["file_name"].encode('utf-8'), voice["preset"].encode('utf-8'))
            min = voice["low_note"]
            max = voice["high_note"]
            volume = int(voice["volume"])
            transpose = int(voice["transpose"])
            route_notes_to_channel(channel, note_to_midi(min), note_to_midi(max), volume, transpose)
            if voice["sustain"]:
                route_sustain_to_channel(channel)


    def apply_reverb(self, reverb_settings):
        print(reverb_settings)
        set_reverb(reverb_settings["room_size"],
                   reverb_settings["damping"],
                   reverb_settings["width"],
                   reverb_settings["level"]
                    )

    def _apply_song_patch_if_any(self, song):
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
                self.apply_patch(
                    [default_voice],
                    None,
                    {
                        'room_size': 0.5,
                        'damping': 0.5,
                        'width': 0.5,
                        'level': 0.9,
                    },
                )
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
        self.apply_patch(voices_data, patch.id, reverb_settings)

    def _activate_first_song_in_active_set(self):
        active = Set.objects.filter(active=True).first()
        if not active:
            latest = Set.objects.order_by('-date').first()
            if not latest:
                return
            latest.active = True
            latest.save()
            active = latest

        ordered = list(SetSong.objects.filter(set=active).select_related('song')
                       .order_by(F('order').asc(nulls_last=True), 'song__name'))
        if not ordered:
            return

        first = ordered[0]
        with transaction.atomic():
            SetSong.objects.filter(set=active).update(active=False)
            SetSong.objects.filter(pk=first.pk).update(active=True)

        self._apply_song_patch_if_any(first.song)

    def get_presets_for_file(self, filename):
        """
        Returns presets for a given soundfont filename as a list of dictionaries.
        Each dict contains: {'bank': int, 'num': int, 'name': str}
        """
        if not filename:
            return []
        
        # Call the C function to get soundfont by name
        soundfont = get_soundfont_by_name(filename.encode('utf-8'))
        if not soundfont:
            return []
        
        # Convert C presets array to Python list of dicts
        presets = []
        for i in range(soundfont.contents.preset_count):
            preset = soundfont.contents.presets[i]
            presets.append({
                'bank': preset.bank,
                'num': preset.num,
                'name': preset.name.decode('utf-8')
            })
        
        return presets

    def cleanup(self):
        print('\nCleaning Up Things....')
        cleanup_midi_device()



