"""
Proof of Concept: Python Metronome Testing
Tests the metronome C module via ctypes
"""

import ctypes
import time
import signal
import sys
import os
from pathlib import Path

# Load the metronome shared library
CFLUID_PATH = Path(__file__).parent.parent / "cfluid"
LIB_PATH = CFLUID_PATH / "libmetronome.so"

if not LIB_PATH.exists():
    print(f"Error: {LIB_PATH} not found")
    print("Please compile the metronome module first with:")
    print("  cd cfluid && make metronome")
    sys.exit(1)

# Load the shared library
lib = ctypes.CDLL(str(LIB_PATH))

# Define the metronome_config_t structure
class MetronomeConfig(ctypes.Structure):
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


class Metronome:
    """Python wrapper for the C metronome module"""

    def __init__(self, config_path="../fluidsynth.cfg", soundfont_path=None):
        """Initialize the metronome"""
        print("Initializing metronome...")
        config_bytes = config_path.encode('utf-8')
        soundfont_bytes = soundfont_path.encode('utf-8') if soundfont_path else None
        
        ret = lib.metronome_init(config_bytes, soundfont_bytes)
        if ret != 0:
            raise RuntimeError("Failed to initialize metronome")
        print("Metronome initialized successfully")

    def start(self, bpm=120, beats_per_measure=4, note_value=4, 
              accent_note=84, normal_note=76, channel=0, bank=0, program=0,
              velocity=100, duration_ms=100):
        """Start the metronome"""
        config = MetronomeConfig(
            bpm=bpm,
            beats_per_measure=beats_per_measure,
            note_value=note_value,
            accent_note=accent_note,
            normal_note=normal_note,
            channel=channel,
            bank=bank,
            program=program,
            velocity=velocity,
            duration_ms=duration_ms,
        )
        
        print(f"Starting metronome: BPM={bpm}, Time Signature={beats_per_measure}/{note_value}, Bank={bank}, Program={program}")
        ret = lib.metronome_start(ctypes.byref(config))
        if ret != 0:
            raise RuntimeError("Failed to start metronome")

    def stop(self):
        """Stop the metronome"""
        print("Stopping metronome...")
        ret = lib.metronome_stop()
        if ret != 0:
            raise RuntimeError("Failed to stop metronome")

    def is_running(self):
        """Check if metronome is running"""
        return lib.metronome_is_running() != 0

    def set_bpm(self, bpm):
        """Update BPM"""
        ret = lib.metronome_set_bpm(bpm)
        if ret != 0:
            raise RuntimeError(f"Failed to set BPM to {bpm}")
        print(f"BPM updated to {bpm}")

    def set_time_signature(self, beats_per_measure, note_value=4):
        """Update time signature"""
        ret = lib.metronome_set_time_signature(beats_per_measure, note_value)
        if ret != 0:
            raise RuntimeError(f"Failed to set time signature to {beats_per_measure}/{note_value}")
        print(f"Time signature updated to {beats_per_measure}/{note_value}")

    def cleanup(self):
        """Clean up metronome resources"""
        print("Cleaning up...")
        ret = lib.metronome_cleanup()
        if ret != 0:
            raise RuntimeError("Failed to cleanup metronome")
        print("Metronome cleaned up successfully")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nReceived interrupt, shutting down...")
    global metronome
    if metronome and metronome.is_running():
        metronome.stop()
    sys.exit(0)


def main():
    """Main test function"""
    global metronome
    
    metronome = None  # Initialize to None
    print("=== Metronome Proof of Concept (Python) ===\n")
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Initialize metronome
        metronome = Metronome()
        
        # Start metronome at 120 BPM, 4/4 time
        # Using Bank 128 (Drums), Program 16 (Power Drums)
        # Ab4 (note 68) for downbeat, Ab3 (note 56) for other beats
        metronome.start(
            bpm=120,
            beats_per_measure=4,
            note_value=4,
            accent_note=68,      # Ab4 - downbeat
            normal_note=56,      # Ab3 - other beats
            channel=0,
            bank=128,            # Drum bank
            program=16,          # Power Drums
            velocity=100,
            duration_ms=200      # 200ms note duration for better audibility
        )
        
        print("\nRunning for 15 seconds...")
        print("- Metronome beats will be printed to console")
        print("- After 5 seconds, BPM will change to 140")
        print("- After 10 seconds, time signature will change to 3/4\n")
        
        # Run for 15 seconds with some dynamic changes
        for elapsed in range(15):
            time.sleep(1)
            print(f"[{elapsed+1}/15 seconds] Running...", end=" ", flush=True)
            
            if elapsed == 4:
                print("\n>>> Changing BPM to 140 <<<")
                metronome.set_bpm(140)
            elif elapsed == 9:
                print("\n>>> Changing time signature to 3/4 <<<")
                metronome.set_time_signature(3, 4)
            else:
                print()
        
        # Stop metronome
        metronome.stop()
        
        # Clean up
        metronome.cleanup()
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if metronome:
            try:
                metronome.cleanup()
            except:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
