"""
Metronome module - provides interface to C metronome library
"""

import ctypes
import os
from pathlib import Path

# Load the metronome shared library
CFLUID_PATH = Path(__file__).parent.parent.parent / "cfluid"
LIB_PATH = CFLUID_PATH / "libmetronome.so"

if not LIB_PATH.exists():
    raise RuntimeError(f"Metronome library not found at {LIB_PATH}. Please build with: cd cfluid && make")

lib = ctypes.CDLL(str(LIB_PATH))


class MetronomeConfig(ctypes.Structure):
    """Configuration structure for metronome"""
    _fields_ = [
        ("bpm", ctypes.c_int),
        ("beats_per_measure", ctypes.c_int),
        ("note_value", ctypes.c_int),
        ("accent_note", ctypes.c_int),
        ("normal_note", ctypes.c_int),
        ("channel", ctypes.c_int),
        ("bank", ctypes.c_int),
        ("program", ctypes.c_int),
        ("velocity", ctypes.c_int),
        ("duration_ms", ctypes.c_int),
        ("cowbell_note", ctypes.c_int),
        ("cowbell_program", ctypes.c_int),
    ]


# Define C function signatures
lib.metronome_init.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
lib.metronome_init.restype = ctypes.c_int

lib.metronome_cleanup.argtypes = []
lib.metronome_cleanup.restype = ctypes.c_int

lib.metronome_start.argtypes = [ctypes.POINTER(MetronomeConfig)]
lib.metronome_start.restype = ctypes.c_int

lib.metronome_stop.argtypes = []
lib.metronome_stop.restype = ctypes.c_int

lib.metronome_is_running.argtypes = []
lib.metronome_is_running.restype = ctypes.c_int

lib.metronome_set_bpm.argtypes = [ctypes.c_int]
lib.metronome_set_bpm.restype = ctypes.c_int

lib.metronome_set_time_signature.argtypes = [ctypes.c_int, ctypes.c_int]
lib.metronome_set_time_signature.restype = ctypes.c_int

lib.metronome_set_gain.argtypes = [ctypes.c_float]
lib.metronome_set_gain.restype = ctypes.c_int


__all__ = [
    'lib',
    'MetronomeConfig',
]
