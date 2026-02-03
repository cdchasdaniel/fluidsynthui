import atexit
import logging
import os
from django.conf import settings
from . import init_midi_device, cleanup_midi_device, set_channel_preset, route_notes_to_channel, route_sustain_to_channel, set_reverb, get_soundfont_by_name, clear_router 

logger = logging.getLogger(__name__)


def note_to_midi(note_str):
    """
    Converts simple notation like 'C5' or 'F#2' to MIDI integers.
    Convention: C0 = 0, C5 = 60.
    """
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    # Map 'b' (flats) to '#' (sharps) for consistency
    flats = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}

    try:
        # Standardize string (e.g., 'bb3' -> 'Bb3')
        note_str = note_str.capitalize()

        # Identify note name vs octave number
        if note_str[1] in ['#', 'b']:
            name = note_str[:2]
            octave = int(note_str[2:])
        else:
            name = note_str[:1]
            octave = int(note_str[1:])

        # Handle flats
        name = flats.get(name, name)

        # Calculation: Octave * 12 + note index
        midi_num = (octave * 12) + notes.index(name)
        return max(0, min(127, midi_num))  # Keep within MIDI 0-127
    except (ValueError, IndexError):
        return 0  # Fallback




class FluidMidiManager:
    def __init__(self):
        # Initialize Synth with soundfont directory
        soundfont_path = os.path.join(settings.BASE_DIR, 'sf')
        self.fs = init_midi_device(soundfont_path.encode('utf-8'))
        self.active_patch_id = None
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




