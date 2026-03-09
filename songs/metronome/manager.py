"""
MetronomeManager - High-level interface for controlling the metronome
"""

import atexit
import logging
from . import lib, MetronomeConfig

logger = logging.getLogger(__name__)


class MetronomeManager:
    """
    Manager class for controlling the metronome.
    
    Provides a high-level Python interface to the C metronome library.
    """

    def __init__(self, config_path="../fluidsynth.cfg", soundfont_path=None):
        """
        Initialize the metronome.
        
        Args:
            config_path: Path to fluidsynth config file
            soundfont_path: Path to soundfont file (or None to use default)
        """
        self.is_initialized = False
        self.is_running = False
        self.current_config = None
        self.current_gain = 5.0  # Default to maximum volume
        
        logger.info("Initializing metronome...")
        config_bytes = config_path.encode('utf-8') if isinstance(config_path, str) else config_path
        soundfont_bytes = soundfont_path.encode('utf-8') if soundfont_path else None
        
        ret = lib.metronome_init(config_bytes, soundfont_bytes)
        if ret != 0:
            raise RuntimeError("Failed to initialize metronome")
        
        self.is_initialized = True
        atexit.register(self.cleanup)
        logger.info("Metronome initialized successfully")

    def start(self, bpm=120, beats_per_measure=4, note_value=4,
              accent_note=68, normal_note=56, channel=0, bank=128, program=16,
              velocity=100, duration_ms=200, cowbell_note=0, cowbell_program=0):
        """
        Start the metronome.
        
        Args:
            bpm: Beats per minute (default: 120)
            beats_per_measure: Beats per measure (default: 4)
            note_value: Note value denominator (default: 4 for quarter notes)
            accent_note: MIDI note for downbeat (default: 68 = Ab4)
            normal_note: MIDI note for other beats (default: 56 = Ab3)
            channel: MIDI channel 0-15 (default: 0)
            bank: MIDI bank number (default: 128 = drums)
            program: MIDI program/preset number (default: 16 = power drums)
            velocity: Note velocity 0-127 (default: 100)
            duration_ms: Note duration in milliseconds (default: 200)
            cowbell_note: MIDI note for cowbell on beat 1 (0 = disabled, default: 0)
            cowbell_program: Program for cowbell if different from main (default: 0 = use main)
        """
        if not self.is_initialized:
            raise RuntimeError("Metronome not initialized")
        
        if self.is_running:
            logger.warning("Metronome already running, stopping first")
            self.stop()
        
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
            cowbell_note=cowbell_note,
            cowbell_program=cowbell_program,
        )
        
        ret = lib.metronome_start(config)
        if ret != 0:
            raise RuntimeError("Failed to start metronome")
        
        self.is_running = True
        self.current_config = {
            'bpm': bpm,
            'beats_per_measure': beats_per_measure,
            'note_value': note_value,
            'accent_note': accent_note,
            'normal_note': normal_note,
            'channel': channel,
            'bank': bank,
            'program': program,
            'cowbell_note': cowbell_note,
            'cowbell_program': cowbell_program,
        }
        
        logger.info(f"Metronome started: BPM={bpm}, Time={beats_per_measure}/{note_value}, Bank={bank}, Program={program}, Cowbell={cowbell_note if cowbell_note > 0 else 'disabled'}")

    def stop(self):
        """Stop the metronome."""
        if not self.is_running:
            logger.warning("Metronome not running")
            return
        
        ret = lib.metronome_stop()
        if ret != 0:
            raise RuntimeError("Failed to stop metronome")
        
        self.is_running = False
        logger.info("Metronome stopped")

    def is_running_check(self):
        """Check if metronome is currently running."""
        if not self.is_initialized:
            return False
        return lib.metronome_is_running() != 0

    def set_bpm(self, bpm):
        """
        Update BPM while metronome is running.
        
        Args:
            bpm: New BPM value
        """
        if bpm <= 0 or bpm > 300:
            raise ValueError(f"Invalid BPM: {bpm} (must be 1-300)")
        
        ret = lib.metronome_set_bpm(bpm)
        if ret != 0:
            raise RuntimeError(f"Failed to set BPM to {bpm}")
        
        if self.current_config:
            self.current_config['bpm'] = bpm
        
        logger.info(f"BPM updated to {bpm}")

    def set_time_signature(self, beats_per_measure, note_value=4):
        """
        Update time signature while metronome is running.
        
        Args:
            beats_per_measure: Beats per measure (1-12)
            note_value: Note value denominator (4, 8, or 16)
        """
        if beats_per_measure <= 0 or beats_per_measure > 12:
            raise ValueError(f"Invalid beats per measure: {beats_per_measure} (must be 1-12)")
        
        if note_value not in [4, 8, 16]:
            raise ValueError(f"Invalid note value: {note_value} (must be 4, 8, or 16)")
        
        ret = lib.metronome_set_time_signature(beats_per_measure, note_value)
        if ret != 0:
            raise RuntimeError(f"Failed to set time signature to {beats_per_measure}/{note_value}")
        
        if self.current_config:
            self.current_config['beats_per_measure'] = beats_per_measure
            self.current_config['note_value'] = note_value
        
        logger.info(f"Time signature updated to {beats_per_measure}/{note_value}")

    def set_gain(self, gain):
        """
        Set metronome synth gain/volume.
        
        Args:
            gain: Gain value (0.0 to 5.0, where 1.0 is normal)
        """
        if gain < 0.0 or gain > 5.0:
            raise ValueError(f"Invalid gain: {gain} (must be 0.0-5.0)")
        
        ret = lib.metronome_set_gain(gain)
        if ret != 0:
            raise RuntimeError(f"Failed to set gain to {gain}")
        
        self.current_gain = gain
        logger.info(f"Metronome gain set to {gain}")

    def cleanup(self):
        """Clean up metronome resources."""
        if not self.is_initialized:
            return
        
        if self.is_running:
            self.stop()
        
        ret = lib.metronome_cleanup()
        if ret != 0:
            raise RuntimeError("Failed to cleanup metronome")
        
        self.is_initialized = False
        logger.info("Metronome cleaned up")

    def __del__(self):
        """Ensure cleanup on object deletion."""
        if self.is_initialized:
            try:
                self.cleanup()
            except Exception as e:
                logger.error(f"Error during metronome cleanup: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False
