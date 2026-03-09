from django import forms

from patches.models import Patch
from .models import Song


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['name', 'notes', 'tempo', 'time_signature', 'patch']

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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Patch is a ForeignKey (many songs can share a patch) — show all patches
        self.fields['patch'].queryset = Patch.objects.all()
        self.fields['patch'].required = False
        self.fields['notes'].required = False
        self.fields['tempo'].required = False