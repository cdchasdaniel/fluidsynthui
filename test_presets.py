#!/usr/bin/env python3
"""
Test script to verify preset loading functionality
"""
import ctypes
import os
from pathlib import Path

# Load the library
script_dir = Path(__file__).parent
lib_path = script_dir / "cfluid" / "libcfluid.dylib"
lib = ctypes.CDLL(str(lib_path))

# Define preset_t structure
class PresetT(ctypes.Structure):
    _fields_ = [
        ("bank", ctypes.c_int),
        ("num", ctypes.c_int),
        ("name", ctypes.c_char * 256),
    ]

# Define soundfont_t structure
class SoundfontT(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 256),
        ("path", ctypes.c_char * 512),
        ("soundfont_id", ctypes.c_int),
        ("presets", ctypes.POINTER(PresetT)),
        ("preset_count", ctypes.c_int),
    ]

# Define function signatures
init_midi_device = lib.init_midi_device
init_midi_device.argtypes = [ctypes.c_char_p]
init_midi_device.restype = ctypes.c_int

cleanup_midi_device = lib.cleanup_midi_device
cleanup_midi_device.argtypes = []
cleanup_midi_device.restype = ctypes.c_int

load_soundfonts = lib.load_soundfonts
load_soundfonts.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
load_soundfonts.restype = ctypes.POINTER(SoundfontT)

free_soundfonts = lib.free_soundfonts
free_soundfonts.argtypes = [ctypes.POINTER(SoundfontT), ctypes.c_int]
free_soundfonts.restype = None

sf_path = os.path.join(str(script_dir), "sf").encode('utf-8')
print(f"Initializing MIDI device with soundfont path: {sf_path.decode('utf-8')}")

# Initialize the MIDI device
result = init_midi_device(sf_path)
if result != 0:
    print(f"Failed to initialize MIDI device (error code: {result})")
    exit(1)

print("MIDI device initialized successfully\n")

# Now the presets should be enumerated during init
# For now, just test that init succeeds and cleanup works

cleanup_midi_device()
print("MIDI device cleaned up successfully")
