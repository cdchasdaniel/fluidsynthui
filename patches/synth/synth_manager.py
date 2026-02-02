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
        print("DEBUG: Clearing router...")
        self.fs.router_clear()
        for voice in voices_data:
            channel = voice["channel"]-1
            sfid = self.all_soundfont_presets[voice["file_name"]]["sfid"]
            preset = voice["preset"].split(":")
            bank = int(preset[0])
            num = int(preset[1])
            print(f"DEBUG: program_select(channel={channel}, sfid={sfid}, bank={bank}, num={num})")
            self.fs.program_select(channel, sfid, bank, num)
            min = voice["low_note"]
            max = voice["high_note"]
            volume = int(voice["volume"])
            transpose = int(voice["transpose"])
            print(f"DEBUG: Setting up routing for channel {channel}: min={min}, max={max}, vol={volume}, transpose={transpose}")
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
        r1 = self.fs.router_begin("note")
        print(f"  router_begin('note') returned: {r1}")
        r2 = self.fs.router_chan(0, 0, 0, channel)
        print(f"  router_chan(0, 0, 0, {channel}) returned: {r2}")
        r3 = self.fs.router_par1(note_to_midi(min), note_to_midi(max), 1.0, transpose)
        print(f"  router_par1 returned: {r3}")
        r4 = self.fs.router_par2(0, 127, 0.0, volume)
        print(f"  router_par2 returned: {r4}")
        r5 = self.fs.router_end()
        print(f"  router_end() returned: {r5}")

    def send_sustain_cc_to_channel_0(self, channel):
        self.fs.router_begin("cc")
        self.fs.router_par1(64, 64, 1.0, 0)
        self.fs.router_chan(0, 0, 0, channel)
        self.fs.router_end()

    def cleanup(self):
        print('\nCleaning Up Things....')
        if hasattr(self, 'fs'): self.fs.delete()



