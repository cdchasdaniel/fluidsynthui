import os
from django.apps import AppConfig
from fluidsynthui import settings
from django.conf import settings as django_settings


class PatchesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'patches'

    def ready(self):
        # The Django autoreloader starts the process twice (monitor + worker).
        # Initialize FluidSynth only in the worker (reloader) process to avoid
        # double initialization and audio-device conflicts.
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            from patches.synth.synth_manager import FluidMidiManager
            synth = FluidMidiManager()
            # Keep both settings access patterns in sync.
            settings.FLUID_SYNTH = synth
            django_settings.FLUID_SYNTH = synth