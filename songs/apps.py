import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class SongsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'songs'

    def ready(self):
        """Initialize the metronome and pad manager when Django starts"""
        print("=== SongsConfig.ready() called ===")
        try:
            from songs.metronome.manager import MetronomeManager
            from songs.pad_manager import PadManager
            from pathlib import Path
            from django.conf import settings
            
            print(f"BASE_DIR: {settings.BASE_DIR}")
            config_path = str(Path(settings.BASE_DIR) / 'fluidsynth.cfg')
            print(f"Config path: {config_path}")
            
            # Create metronome instance
            print("Creating MetronomeManager...")
            metronome = MetronomeManager(
                config_path=config_path,
                soundfont_path=None
            )
            print(f"MetronomeManager created: {metronome}")
            
            # Store in settings for app-wide access
            settings.METRONOME_MANAGER = metronome
            print(f"Stored in settings.METRONOME_MANAGER: {settings.METRONOME_MANAGER}")
            logger.info("Metronome manager initialized and stored in settings")
            
            # Create pad manager instance (non-fatal if fails)
            print("Creating PadManager...")
            pad_manager = PadManager()
            print(f"PadManager created: {pad_manager}")
            
            # Store in settings for app-wide access
            settings.PAD_MANAGER = pad_manager
            print(f"Stored in settings.PAD_MANAGER: {settings.PAD_MANAGER}")
            if pad_manager.initialized:
                logger.info("Pad manager initialized and stored in settings")
            else:
                logger.warning("Pad manager failed to initialize, but app will continue")
            
        except Exception as e:
            print(f"ERROR initializing managers: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Failed to initialize managers: {e}")
            # Don't raise - allow app to continue without managers if initialization fails
