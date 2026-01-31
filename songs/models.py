from django.db import models

from patches.models import Patch


class Song(models.Model):
    name = models.CharField(max_length=200)
    notes = models.CharField(max_length=500,null=True)
    tempo = models.IntegerField(null=True)
    # Allow multiple songs to reference the same Patch (many-to-one)
    patch = models.ForeignKey(Patch, on_delete=models.CASCADE, null=True, blank=True, related_name='songs')

    def __str__(self):
        return self.name