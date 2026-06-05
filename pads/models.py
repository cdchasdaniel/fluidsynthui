from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Pad(models.Model):
    """
    A sustained chord pad: multiple MIDI notes from a single soundfont/preset
    that plays indefinitely until stopped.
    """
    name = models.CharField(max_length=200)
    file_name = models.CharField(max_length=255)  # Soundfont filename (e.g., "defaultGM.sf2")
    preset = models.CharField(max_length=255, default="000:000")  # "bank:program"
    preset_name = models.CharField(max_length=200, blank=True)  # Display name (e.g., "Grand Piano")
    
    # JSON string storing list of MIDI note numbers, e.g., "[60, 64, 67]"
    # Represents a chord (C, E, G in this example)
    notes_json = models.TextField(default="[60]")
    
    # Velocity/volume for all notes in the chord
    velocity = models.PositiveIntegerField(
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(127)]
    )
    
    # Fade-in duration in seconds (0 = instant)
    fade_in_duration = models.FloatField(default=0, validators=[MinValueValidator(0)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.preset})"
    
    def get_notes(self):
        """Parse notes_json and return list of MIDI note integers."""
        import json
        try:
            return json.loads(self.notes_json)
        except (json.JSONDecodeError, TypeError):
            return [60]  # Default to C4 if parsing fails
    
    def set_notes(self, notes_list):
        """Store notes as JSON string."""
        import json
        self.notes_json = json.dumps(notes_list)
