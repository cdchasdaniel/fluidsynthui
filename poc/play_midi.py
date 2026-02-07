#!/usr/bin/env python3
"""
Python interface to call the FluidSynth MIDI player from C
"""

import ctypes
import time
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent

# Load the shared library
lib_path = script_dir.parent / "cfluid" / "libcfluid.so"
if not lib_path.exists():
    raise FileNotFoundError(f"Library not found at {lib_path}. Please run 'make lib' in the cfluid directory first.")

lib = ctypes.CDLL(str(lib_path))

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

# int set_reverb(double room_size, double damping, double width, double level);
set_reverb = lib.set_reverb
set_reverb.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
set_reverb.restype = ctypes.c_int

def main():
    """Start the MIDI device listener"""
    print("Starting MIDI device listener...")
    
    # Initialize the MIDI device with config path
    config_path = script_dir.parent / "fluidsynth.cfg"
    result = init_midi_device(str(config_path).encode('utf-8'))
    if result != 0:
        print("Failed to initialize MIDI device")
        return 1
    
    print("MIDI device initialized.")
    
    # Apply reverb for a richer sound
    print("Applying reverb...")
    result = set_reverb(1.0, 0.5, 0.9, 0.9)  # room_size, damping, width, level
    if result != 0:
        print("Failed to set reverb")
        return 1
    
    # Set up layered sounds: Piano on channel 1, Strings on channel 2
    print("Setting up piano on channel 1...")
    result = set_channel_preset(1, b"defaultGM.sf2", b"0:0")  # Acoustic Grand Piano
    if result != 0:
        print("Failed to set piano preset")
        return 1
    
    print("Setting up strings on channel 2...")
    result = set_channel_preset(2, b"defaultGM.sf2", b"0:48")  # String Ensemble 1
    if result != 0:
        print("Failed to set strings preset")
        return 1
    
    # Route MIDI channel 0 notes to both channels for layering
    # Route all notes (0-127) to channel 1 (piano) with no transpose, normal volume
    print("Routing notes to piano channel...")
    result = route_notes_to_channel(1, 0, 127, 0, 0)
    if result != 0:
        print("Failed to route to piano channel")
        return 1
    
    # Route all notes (0-127) to channel 2 (strings) with no transpose, slightly lower volume
    print("Routing notes to strings channel...")
    result = route_notes_to_channel(2, 0, 127, -20, 0)
    if result != 0:
        print("Failed to route to strings channel")
        return 1
    
    # Route sustain pedal to both channels
    print("Routing sustain pedal to piano channel...")
    result = route_sustain_to_channel(1)
    if result != 0:
        print("Failed to route sustain to piano channel")
        return 1
    
    print("Routing sustain pedal to strings channel...")
    result = route_sustain_to_channel(2)
    if result != 0:
        print("Failed to route sustain to strings channel")
        return 1
    
    print("Layered piano + strings ready!")
    print("Play notes on your MIDI device (press Ctrl+C to stop)")
    
    try:
        # Keep the loop running in Python so Ctrl+C works
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        # Clean up
        cleanup_midi_device()
        print("MIDI device closed.")
    
    return 0

if __name__ == "__main__":
    exit(main())
