from django import forms
from mp3.utils import get_mp3_directory

from patches.models import Patch
from pads.models import Pad
from .models import Song


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = [
            'name',
            'notes',
            'tempo',
            'time_signature',
            'patch',
            'pad',
            'mp3_slot_1',
            'mp3_slot_2',
            'mp3_slot_3',
            'mp3_slot_4',
            'mp3_slot_5',
            'mp3_slot_6',
            'mp3_slot_7',
            'mp3_slot_8',
        ]

        widgets = {
            # Standard Title Input
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter song title...',
                'autofocus': 'autofocus'
            }),

            # Larger area for performance instructions
            'notes': forms.Textarea(attrs={
                'class': 'form-control notes-area',
                'placeholder': 'Key changes, structure, or performance tips...',
                'rows': 3
            }),

            # Narrow DAW-style number input
            'tempo': forms.NumberInput(attrs={
                'class': 'form-control tempo-input mx-auto',
                'min': '40',
                'max': '250'
            }),

            # Time Signature toggle
            'time_signature': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),

            # Dropdown for Patch selection
            'patch': forms.Select(attrs={
                'class': 'form-select patch-select-width'
            }),
            # Dropdown for Pad selection
            'pad': forms.Select(attrs={
                'class': 'form-select patch-select-width'
            }),
            'mp3_slot_1': forms.Select(attrs={'class': 'form-select'}),
            'mp3_slot_2': forms.Select(attrs={'class': 'form-select'}),
            'mp3_slot_3': forms.Select(attrs={'class': 'form-select'}),
            'mp3_slot_4': forms.Select(attrs={'class': 'form-select'}),
            'mp3_slot_5': forms.Select(attrs={'class': 'form-select'}),
            'mp3_slot_6': forms.Select(attrs={'class': 'form-select'}),
            'mp3_slot_7': forms.Select(attrs={'class': 'form-select'}),
            'mp3_slot_8': forms.Select(attrs={'class': 'form-select'}),
        }

        labels = {
            'mp3_slot_1': 'Button 1 (CC16)',
            'mp3_slot_2': 'Button 2 (CC17)',
            'mp3_slot_3': 'Button 3 (CC18)',
            'mp3_slot_4': 'Button 4 (CC19)',
            'mp3_slot_5': 'Button 5 (CC20)',
            'mp3_slot_6': 'Button 6 (CC21)',
            'mp3_slot_7': 'Button 7 (CC22)',
            'mp3_slot_8': 'Button 8 (CC23)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Patch is a ForeignKey (many songs can share a patch) — show all patches
        self.fields['patch'].queryset = Patch.objects.all()
        self.fields['patch'].required = False
        
        # Pad is a ForeignKey (many songs can share a pad) — show all pads
        self.fields['pad'].queryset = Pad.objects.all()
        self.fields['pad'].required = False
        
        self.fields['notes'].required = False
        self.fields['tempo'].required = False

        mp3_dir = get_mp3_directory()
        choices = [('', 'No File')]
        files = {
            f.name for f in mp3_dir.iterdir()
            if f.is_file() and f.suffix.lower() == '.mp3'
        }
        choices.extend((name, name) for name in sorted(files, key=str.casefold))

        for idx in range(1, 9):
            field_name = f'mp3_slot_{idx}'
            existing_value = None
            if self.instance and getattr(self.instance, 'pk', None):
                existing_value = getattr(self.instance, field_name, None)

            self.fields[field_name] = forms.ChoiceField(
                required=False,
                choices=choices,
                label=self.Meta.labels[field_name],
                widget=forms.Select(attrs={'class': 'form-select'}),
                initial=existing_value,
            )