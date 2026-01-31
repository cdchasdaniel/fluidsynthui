from django.apps import AppConfig
from bob import settings
from patches.synth.synth_manager import FluidMidiManager


class PatchesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'patches'
    settings.FLUID_SYNTH = FluidMidiManager()