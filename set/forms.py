from django import forms

from .models import Set
from songs.models import Song


class SetForm(forms.ModelForm):
    class Meta:
        model = Set
        fields = ['name', 'location', 'date', 'description']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter set name...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Venue or location (optional)'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional fields
        self.fields['description'].required = False
        # Location is optional
        self.fields['location'].required = False
