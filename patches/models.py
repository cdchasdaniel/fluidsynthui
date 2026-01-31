from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models


class Patch(models.Model):
    name = models.CharField(max_length=200)
    # Global Reverb Settings
    reverb_room_size = models.FloatField(default=0.5) # 0.0 - 1.2
    reverb_damping = models.FloatField(default=0.5)   # 0.0 - 1.0
    reverb_width = models.FloatField(default=0.5)     # 0.0 - 100.0
    reverb_level = models.FloatField(default=0.0)     # 0.0 - 1.0

    def __str__(self):
        return self.name

# Matches C0, F#2, Bb7, etc. (No spaces, no dashes)
# ^[A-Ga-g]   -> Note name
# [#b]?       -> Optional Sharp or Flat
# [0-9]       -> Octave 0 through 9
simple_note_validator = RegexValidator(
    regex=r'^[A-Ga-g][#b]?[0-9]$',
    message="Enter note and octave (e.g., C4, F#2, Bb0)."
)


class Voice(models.Model):
    patch = models.ForeignKey(Patch, on_delete=models.CASCADE, related_name='voices')
    channel = models.IntegerField()
    file_name = models.CharField(max_length=255)
    # Stores combined string like "001:032"
    preset = models.CharField(max_length=255, default="000:000")
    # Stores display name like "Grand Piano"
    preset_name = models.CharField(max_length=200, blank=True)
    # MIDI Standard Volume (CC 7)
    volume = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(127)]
    )
    transpose = models.IntegerField(
        default=0,
        validators=[MinValueValidator(-24), MaxValueValidator(24)]
    )
    sustain = models.BooleanField(default=True)  # Whether to respond to sustain pedal

    # Keyboard Range (Scientific Pitch Notation)
    low_note = models.CharField(
        max_length=3,
        default="C0",
        validators=[simple_note_validator]
    )
    high_note = models.CharField(
        max_length=3,
        default="G9", # MIDI 127 is roughly G9
        validators=[simple_note_validator]
    )

    def __str__(self):
        return f"Voice {self.channel}: {self.preset}"


