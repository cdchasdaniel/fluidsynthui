from django.db import models

from patches.models import Patch
from pads.models import Pad


class Song(models.Model):
    TIME_SIGNATURE_CHOICES = [
        ('4/4', '4/4 (Common Time)'),
        ('6/8', '6/8 (Compound Time)'),
    ]

    name = models.CharField(max_length=200)
    notes = models.CharField(max_length=500, null=True)
    tempo = models.IntegerField(null=True)
    time_signature = models.CharField(
        max_length=10,
        choices=TIME_SIGNATURE_CHOICES,
        default='4/4'
    )
    # Allow multiple songs to reference the same Patch (many-to-one)
    patch = models.ForeignKey(Patch, on_delete=models.CASCADE, null=True, blank=True, related_name='songs')
    # Optional pad (sustained chord background)
    pad = models.ForeignKey(Pad, on_delete=models.SET_NULL, null=True, blank=True, related_name='songs')
    mp3_slot_1 = models.CharField(max_length=255, null=True, blank=True)
    mp3_slot_2 = models.CharField(max_length=255, null=True, blank=True)
    mp3_slot_3 = models.CharField(max_length=255, null=True, blank=True)
    mp3_slot_4 = models.CharField(max_length=255, null=True, blank=True)
    mp3_slot_5 = models.CharField(max_length=255, null=True, blank=True)
    mp3_slot_6 = models.CharField(max_length=255, null=True, blank=True)
    mp3_slot_7 = models.CharField(max_length=255, null=True, blank=True)
    mp3_slot_8 = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name