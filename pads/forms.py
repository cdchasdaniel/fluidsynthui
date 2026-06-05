from django import forms
from .models import Pad
import json
from pathlib import Path
from fluidsynthui import settings
from patches.forms import get_soundfont_dir, get_sf2_choices
from patches.utils import note_to_midi


def midi_to_note(midi_num):
    """Converts MIDI number to note name (e.g., 60 -> C4)"""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = midi_num // 12
    note = notes[midi_num % 12]
    return f"{note}{octave}"


class PadForm(forms.ModelForm):
    # Display notes as comma-separated note names (C4, Db5, etc.)
    notes_display = forms.CharField(
        label="Notes (e.g., C4, E4, G4 or C4, Eb4, G4)",
        help_text="Use note names like C4, D5, F#3, Bb2, etc. (sharps # or flats b)",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'C4, E4, G4'})
    )
    
    file_name = forms.ChoiceField(
        choices=[],  # Will be populated in __init__
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Pad
        fields = ['name', 'file_name', 'preset', 'preset_name', 'notes_display', 'velocity', 'fade_in_duration']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Ambient Pad'}),
            'preset': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000:000'}),
            'preset_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Display name'}),
            'velocity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 127}),
            'fade_in_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.1, 'placeholder': 'Seconds'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamically populate soundfont choices
        sf_dir = str(get_soundfont_dir())
        self.fields['file_name'].choices = get_sf2_choices(sf_dir)
        
        # For editing, convert saved MIDI notes to note names for display
        if self.instance and self.instance.pk and not self.data:
            try:
                notes_list = json.loads(self.instance.notes_json)
                note_names = [midi_to_note(int(n)) for n in notes_list]
                self.fields['notes_display'].initial = ', '.join(note_names)
            except (json.JSONDecodeError, TypeError, ValueError):
                self.fields['notes_display'].initial = 'C4'

    def clean_notes_display(self):
        notes_str = self.cleaned_data.get('notes_display', '')
        try:
            note_names = [n.strip() for n in notes_str.split(',') if n.strip()]
            if not note_names:
                raise ValueError("At least one note required")
            
            # Convert note names to MIDI numbers
            midi_notes = []
            for note_name in note_names:
                midi_num = note_to_midi(note_name)
                if midi_num < 0 or midi_num > 127:
                    raise ValueError(f"{note_name} is out of MIDI range (0-127)")
                midi_notes.append(midi_num)
            
            return midi_notes
        except (ValueError, TypeError) as e:
            raise forms.ValidationError(f"Invalid notes: {e}")

    def save(self, commit=True):
        instance = super().save(commit=False)
        notes_list = self.cleaned_data.get('notes_display', [60])
        instance.notes_json = json.dumps(notes_list)
        if commit:
            instance.save()
        return instance
