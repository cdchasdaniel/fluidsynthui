# soundfount.py
import ctypes
import os
import re

import fluidsynth
from fluidsynth import _fl

from bob import settings

# --- Define C-Signatures for SoundFont Inspection ---
_fl.fluid_synth_get_sfont_by_id.argtypes = [ctypes.c_void_p, ctypes.c_uint]
_fl.fluid_synth_get_sfont_by_id.restype = ctypes.c_void_p

_fl.fluid_sfont_iteration_start.argtypes = [ctypes.c_void_p]
_fl.fluid_sfont_iteration_next.argtypes = [ctypes.c_void_p]
_fl.fluid_sfont_iteration_next.restype = ctypes.c_void_p

_fl.fluid_preset_get_name.argtypes = [ctypes.c_void_p]
_fl.fluid_preset_get_name.restype = ctypes.c_char_p
_fl.fluid_preset_get_banknum.argtypes = [ctypes.c_void_p]
_fl.fluid_preset_get_banknum.restype = ctypes.c_int
_fl.fluid_preset_get_num.argtypes = [ctypes.c_void_p]
_fl.fluid_preset_get_num.restype = ctypes.c_int


def get_presets_from_file(sf_path):
    """
    Scans a .sf2 file and returns a list of its internal presets.
    Takes a fluidsynth.Synth instance and the absolute path to the file.
    """
    sf_path = "sf/"+sf_path
    if not os.path.exists(sf_path):
        print(f"file not found {sf_path}")
        return []

    # Initialize Synth (No audio driver needed just for scanning)
    fs = fluidsynth.Synth()

    # 1. Load temporarily to scan
    temp_id = fs.sfload(sf_path)
    if temp_id == -1:
        return []

    # 2. Get C-pointer to the SoundFont
    sfont = _fl.fluid_synth_get_sfont_by_id(fs.synth, temp_id)

    presets = []
    if sfont:
        _fl.fluid_sfont_iteration_start(sfont)
        while True:
            preset_ptr = _fl.fluid_sfont_iteration_next(sfont)
            if not preset_ptr:
                break

            presets.append({
                'bank': _fl.fluid_preset_get_banknum(preset_ptr),
                'num': _fl.fluid_preset_get_num(preset_ptr),
                'name': _fl.fluid_preset_get_name(preset_ptr).decode('utf-8'),
            })

    # 3. Unload to free memory
    fs.sfunload(temp_id)
    return sorted(presets, key=lambda x: (x['bank'], x['num']))


def load_soundfont_presets(synth_manager):
    all_soundfont_presets = {}
    SF_DIR = os.path.join(settings.BASE_DIR, settings.SOUNDFONT_DIR)
    sf_files = sorted(os.listdir(SF_DIR))

    # Print each name
    for sf_file in sf_files:
        full_sf_path = os.path.join(settings.BASE_DIR, 'sf', sf_file)
        sfid = synth_manager.fs.sfload(full_sf_path)
        all_soundfont_presets[sf_file] = {'sfid': sfid,
                                          'presets': get_presets_from_file(sf_file)}
    return all_soundfont_presets


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
