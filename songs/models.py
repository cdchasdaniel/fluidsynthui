from django.db import models

from patches.models import Patch


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

    def __str__(self):
        return self.name