# forms.py
import os
from pathlib import Path

from django import forms
from django.forms import inlineformset_factory

from fluidsynthui import settings
from .models import Patch, Voice


class PatchForm(forms.ModelForm):
    class Meta:
        model = Patch
        fields = ['name', 'reverb_room_size', 'reverb_damping', 'reverb_width', 'reverb_level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-lg text-center', 'placeholder': 'Enter Patch Name...'}),
            # Reverb Sliders
            'reverb_room_size': forms.NumberInput(attrs={'type': 'range', 'class': 'form-range', 'min': '0', 'max': '1.2', 'step': '0.01'}),
            'reverb_damping': forms.NumberInput(attrs={'type': 'range', 'class': 'form-range', 'min': '0', 'max': '1.0', 'step': '0.01'}),
            'reverb_width': forms.NumberInput(attrs={'type': 'range', 'class': 'form-range', 'min': '0', 'max': '100', 'step': '1'}),
            'reverb_level': forms.NumberInput(attrs={'type': 'range', 'class': 'form-range', 'min': '0', 'max': '1.0', 'step': '0.01'}),
        }

def get_sf2_choices(directory):
    # Generates a list of (filename, filename) tuples for the dropdown
    path = Path(directory)
    return [(f.name, f.name) for f in path.iterdir() if f.suffix == '.sf2' and f.is_file()]

# forms.py
class VoiceForm(forms.ModelForm):
    # Dynamically find the project 'sf' directory
    SF_DIR = os.path.join(settings.BASE_DIR, settings.SOUNDFONT_DIR)

    file_name = forms.ChoiceField(
        choices=get_sf2_choices(SF_DIR),
        widget=forms.Select(attrs={'class': 'form-select sf-select-width'})
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            name = self.instance.preset_name or ""
            try:
                bank_str, num_str = self.instance.preset.split(':')
                formatted_id = f"{int(bank_str)}:{int(num_str)}"
                self.initial['preset'] = f"{name} {formatted_id}".strip()
            except (ValueError, AttributeError):
                self.initial['preset'] = self.instance.preset

    class Meta:
        model = Voice
        # 1. Add 'volume' to fields
        fields = [
            'channel', 'file_name', 'preset', 'volume',
            'transpose', 'low_note', 'high_note', 'sustain'
        ]
        widgets = {
            'channel': forms.NumberInput(attrs={
                'class': 'form-control narrow-ch',
                'min': '1',        # Limits UI spinner minimum
                'max': '16',       # Limits UI spinner maximum
                'value': '1',       # Sets the default for new voices to 1
                'readonly': 'readonly',
            }),
            'file_name': forms.Select(attrs={'class': 'form-select sf-select-width'}),
            'preset': forms.TextInput(attrs={'class': 'form-control pre-width'}),
            'sustain': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # 2. Define the range slider widget
            'volume': forms.NumberInput(attrs={
                'type': 'range',
                'class': 'form-range',
                'min': '0',
                'max': '127',
                'step': '1',
                'style': 'width: 100px;'
            }),
            'transpose': forms.NumberInput(attrs={
                'class': 'form-control narrow-ch',
                'min': '-24', 'max': '24', 'step': '1'
            }),
            'low_note': forms.TextInput(attrs={
                'class': 'form-control narrow-ch', 'placeholder': 'C0'
            }),
            'high_note': forms.TextInput(attrs={
                'class': 'form-control narrow-ch', 'placeholder': 'G10'
            }),
        }



VoiceFormSet = inlineformset_factory(
    Patch,
    Voice,
    form=VoiceForm,
    extra=0,
    can_delete=True
)


# Add Clean method to enforce the 1-16 range on the server side
def clean_channel(self):
    channel = self.cleaned_data.get('channel')
    if channel < 1 or channel > 16:
        raise forms.ValidationError("MIDI Channel must be between 1 and 16.")
    return channel