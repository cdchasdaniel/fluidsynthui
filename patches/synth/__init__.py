#!/usr/bin/env python3
"""
Python interface to call the FluidSynth MIDI player from C
"""

import ctypes
import time
import platform
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent.parent

# Choose and load primary synth library.
lib_candidates = []
if platform.system() == "Darwin":
    # Prefer .so because our local Makefile rebuild updates this file.
    lib_candidates = ["libcfluid.so", "libcfluid.dylib"]
else:
    lib_candidates = ["libcfluid.so"]

lib = None
loaded_from = None
for candidate in lib_candidates:
    lib_path = script_dir.parent / "cfluid" / candidate
    if lib_path.exists():
        lib = ctypes.CDLL(str(lib_path))
        loaded_from = lib_path
        break

if lib is None:
    raise FileNotFoundError(
        f"Library not found. Tried: {', '.join(str(script_dir.parent / 'cfluid' / c) for c in lib_candidates)}"
    )

print(f"[cfluid] Loaded library: {loaded_from}")


def _resolve_symbol(symbol_name):
    """Resolve symbol from primary lib, then fallback candidates if needed."""
    try:
        return getattr(lib, symbol_name)
    except AttributeError:
        for candidate in lib_candidates:
            lib_path = script_dir.parent / "cfluid" / candidate
            if not lib_path.exists():
                continue
            try:
                alt_lib = ctypes.CDLL(str(lib_path))
                return getattr(alt_lib, symbol_name)
            except AttributeError:
                continue
        raise

# Define C structures
class PresetT(ctypes.Structure):
    _fields_ = [
        ("bank", ctypes.c_int),
        ("num", ctypes.c_int),
        ("name", ctypes.c_char * 256),
    ]

class SoundfontT(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 256),
        ("path", ctypes.c_char * 512),
        ("soundfont_id", ctypes.c_int),
        ("presets", ctypes.POINTER(PresetT)),
        ("preset_count", ctypes.c_int),
    ]

# Define the C function signatures
# int init_midi_device(const char *config_path);
init_midi_device = lib.init_midi_device
init_midi_device.argtypes = [ctypes.c_char_p]
init_midi_device.restype = ctypes.c_int

# int cleanup_midi_device(void);
cleanup_midi_device = lib.cleanup_midi_device
cleanup_midi_device.argtypes = []
cleanup_midi_device.restype = ctypes.c_int

# int set_channel_preset(int channel_num, const char *soundfont_name, const char *preset_name);
set_channel_preset = lib.set_channel_preset
set_channel_preset.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p]
set_channel_preset.restype = ctypes.c_int

# int route_notes_to_channel(int channel, int min_note, int max_note, int volume, int transpose);
route_notes_to_channel = lib.route_notes_to_channel
route_notes_to_channel.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
route_notes_to_channel.restype = ctypes.c_int

# int route_sustain_to_channel(int channel);
route_sustain_to_channel = lib.route_sustain_to_channel
route_sustain_to_channel.argtypes = [ctypes.c_int]
route_sustain_to_channel.restype = ctypes.c_int

# int clear_router(void);
clear_router = lib.clear_router
clear_router.argtypes = []
clear_router.restype = ctypes.c_int

# int set_reverb(double room_size, double damping, double width, double level);
set_reverb = lib.set_reverb
set_reverb.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
set_reverb.restype = ctypes.c_int

# soundfont_t* get_soundfont_by_name(const char *filename);
get_soundfont_by_name = lib.get_soundfont_by_name
get_soundfont_by_name.argtypes = [ctypes.c_char_p]
get_soundfont_by_name.restype = ctypes.POINTER(SoundfontT)

# int get_soundfont_count(void);
get_soundfont_count = lib.get_soundfont_count
get_soundfont_count.argtypes = []
get_soundfont_count.restype = ctypes.c_int

# int play_mp3_file(const char *file_path);
play_mp3_file = _resolve_symbol('play_mp3_file')
play_mp3_file.argtypes = [ctypes.c_char_p]
play_mp3_file.restype = ctypes.c_int

# int stop_mp3_playback(void);
stop_mp3_playback = _resolve_symbol('stop_mp3_playback')
stop_mp3_playback.argtypes = []
stop_mp3_playback.restype = ctypes.c_int

# int set_mp3_slot_path(int slot, const char *file_path);
set_mp3_slot_path = _resolve_symbol('set_mp3_slot_path')
set_mp3_slot_path.argtypes = [ctypes.c_int, ctypes.c_char_p]
set_mp3_slot_path.restype = ctypes.c_int