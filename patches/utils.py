import re


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


def pull_out_preset(voice):
    full_string = voice.preset  # Example: "Grand Piano 0:18"
    # Pattern: (.*?) captures the name, (\d+) captures bank, (\d+) captures preset
    match = re.search(r'^(.*?)\s*(\d+):(\d+)$', full_string)
    if match:
        print("regex success")
        name_part, bank_str, num_str = match.groups()

        # Store the human-readable name in the preset_name field
        voice.preset_name = name_part.strip()

        # Convert the preset field to your standard "000:000" format
        voice.preset = f"{int(bank_str):03d}:{int(num_str):03d}"
    else:
        # Fallback if parsing fails
        voice.preset_name = full_string  # Keep the whole string if unparseable
        voice.preset = "000:000"
