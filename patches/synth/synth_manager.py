import atexit
import logging
import fluidsynth
from patches.synth.soundfont import load_soundfont_presets

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
        # Initialize Synth
        self.fs = fluidsynth.Synth()
        self.fs.setting('midi.autoconnect', 1)
        self.fs.start()
        self.all_soundfont_presets = load_soundfont_presets(self)
        sfid = self.all_soundfont_presets["defaultGM.sf2"]["sfid"]
        self.fs.program_select(0, sfid, 0, 1)
        self.active_patch_id = None
        atexit.register(self.cleanup)

    def apply_patch(self, voices_data, patch_id, reverb_settings):
        if patch_id:
            self.active_patch_id = patch_id
        self.apply_reverb(reverb_settings)
        self.fs.router_clear()
        for voice in voices_data:
            channel = voice["channel"]-1
            sfid = self.all_soundfont_presets[voice["file_name"]]["sfid"]
            preset = voice["preset"].split(":")
            bank = int(preset[0])
            num = int(preset[1])
            self.fs.program_select(channel, sfid, bank, num)
            min = voice["low_note"]
            max = voice["high_note"]
            volume = int(voice["volume"])
            transpose = int(voice["transpose"])
            self.send_all_notes_to_channel_0(channel, min, max, volume, transpose)
            if voice["sustain"]:
                self.send_sustain_cc_to_channel_0(channel)

    def apply_reverb(self, reverb_settings):
        print(reverb_settings)
        self.fs.set_reverb(reverb_settings["room_size"],
                           reverb_settings["damping"],
                           reverb_settings["width"],
                           reverb_settings["level"]
                           )

    def send_all_notes_to_channel_0(self, channel, min, max, volume, transpose):
        self.fs.router_begin("note")
        self.fs.router_chan(0, 0, 0, channel)
        self.fs.router_par1(note_to_midi(min),note_to_midi(max), 1.0, transpose)
        self.fs.router_par2(0, 127, 0.0, volume)
        self.fs.router_end()

    def send_sustain_cc_to_channel_0(self, channel):
        self.fs.router_begin("cc")
        self.fs.router_par1(64, 64, 1.0, 0)
        self.fs.router_chan(0, 0, 0, channel)
        self.fs.router_end()

    def cleanup(self):
        print('\nCleaning Up Things....')
        if hasattr(self, 'fs'): self.fs.delete()



