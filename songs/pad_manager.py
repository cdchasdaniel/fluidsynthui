import os
import json
import logging
from pathlib import Path
from ctypes import c_int, c_char_p, POINTER, Structure
from django.conf import settings

logger = logging.getLogger(__name__)


class PadConfig(Structure):
    """C structure for pad_config_t"""
    pass


PadConfig._fields_ = [
    ("bpm", c_int),
    ("notes", POINTER(c_int)),
    ("note_count", c_int),
    ("velocity", c_int),
    ("sustain", c_int),
    ("duration_ms", c_int),
    ("fade_in_ms", c_int),
]


class PadManager:
    """Manages pad playback using a separate FluidSynth instance."""
    
    def __init__(self):
        """Initialize the pad manager library."""
        self.lib = None
        self.is_playing = False
        self.current_config = None
        self.initialized = False
        
        # Load the pad manager C library
        pad_lib_path = os.path.join(settings.BASE_DIR, 'cfluid', 'libpad.so')
        try:
            import ctypes
            self.lib = ctypes.CDLL(pad_lib_path)
            logger.info(f"[Pad] Loaded library: {pad_lib_path}")
            
            # Define C function signatures
            self.lib.pad_manager_init.argtypes = [c_char_p, c_char_p]
            self.lib.pad_manager_init.restype = c_int
            
            self.lib.pad_manager_cleanup.argtypes = []
            self.lib.pad_manager_cleanup.restype = c_int
            
            self.lib.pad_start.argtypes = [POINTER(PadConfig), c_char_p, c_char_p]
            self.lib.pad_start.restype = c_int
            
            self.lib.pad_stop.argtypes = []
            self.lib.pad_stop.restype = c_int
            
            self.lib.pad_is_playing.argtypes = []
            self.lib.pad_is_playing.restype = c_int
            
            # Initialize pad manager
            config_path = os.path.join(settings.BASE_DIR, 'fluidsynth.cfg')
            print(f"[Pad] Calling pad_manager_init with config: {config_path}")
            result = self.lib.pad_manager_init(
                config_path.encode('utf-8'),
                None  # Use default soundfont path
            )
            
            print(f"[Pad] pad_manager_init returned: {result}")
            if result != 0:
                logger.error(f"[Pad] Failed to initialize pad manager (C returned error code: {result})")
                print(f"[Pad] ERROR: pad_manager_init failed with code {result}")
                self.initialized = False
            else:
                logger.info("[Pad] Manager initialized successfully")
                print("[Pad] SUCCESS: Manager initialized")
                self.initialized = True
            
        except Exception as e:
            logger.error(f"[Pad] Error loading pad library: {e}")
            self.initialized = False
    
    def start_pad(self, pad_obj):
        """
        Start playing a pad.
        
        Args:
            pad_obj: Pad model instance from Django ORM
        
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized or not self.lib:
            logger.warning("[Pad] Pad manager not initialized, cannot start pad")
            return False
        
        try:
            # Parse notes from pad
            notes_list = pad_obj.get_notes()
            if not notes_list:
                logger.warning("[Pad] No notes to play")
                return False
            
            # Create C array of notes
            import ctypes
            notes_array = (c_int * len(notes_list))(*notes_list)
            
            # Create pad config
            config = PadConfig()
            config.bpm = 120  # Dummy value for now
            config.notes = notes_array
            config.note_count = len(notes_list)
            config.velocity = pad_obj.velocity
            config.sustain = 1  # Always sustain indefinitely
            config.duration_ms = 0
            config.fade_in_ms = int(pad_obj.fade_in_duration * 1000)  # Convert seconds to ms
            
            # Call C function
            result = self.lib.pad_start(
                ctypes.byref(config),
                pad_obj.file_name.encode('utf-8'),
                pad_obj.preset.encode('utf-8')
            )
            
            if result == 0:
                self.is_playing = True
                self.current_config = config
                logger.info(f"[Pad] Started pad: {pad_obj.name}")
                return True
            else:
                logger.error(f"[Pad] Failed to start pad: {pad_obj.name}")
                return False
        
        except Exception as e:
            logger.error(f"[Pad] Error starting pad: {e}")
            return False
    
    def stop_pad(self):
        """
        Stop playing the current pad.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized or not self.lib:
            logger.warning("[Pad] Pad manager not initialized, cannot stop pad")
            return False
        
        try:
            result = self.lib.pad_stop()
            if result == 0:
                self.is_playing = False
                self.current_config = None
                logger.info("[Pad] Stopped pad")
                return True
            else:
                logger.error("[Pad] Failed to stop pad")
                return False
        
        except Exception as e:
            logger.error(f"[Pad] Error stopping pad: {e}")
            return False
    
    def is_pad_playing(self):
        """Check if a pad is currently playing."""
        if not self.initialized or not self.lib:
            return False
        
        try:
            return bool(self.lib.pad_is_playing())
        except Exception as e:
            logger.error(f"[Pad] Error checking pad status: {e}")
            return False
    
    def cleanup(self):
        """Clean up pad manager resources."""
        if self.lib:
            try:
                self.lib.pad_manager_cleanup()
                logger.info("[Pad] Cleaned up")
            except Exception as e:
                logger.error(f"[Pad] Error during cleanup: {e}")
