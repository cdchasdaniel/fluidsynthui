from django.db import models
from django.utils import timezone


class Set(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField(default=timezone.now)
    description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    songs = models.ManyToManyField('songs.Song', blank=True, related_name='sets', through='SetSong')
    # Mark which Set is currently active (only one may be True at a time)
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ['date', 'name']
        verbose_name = 'Set'
        verbose_name_plural = 'Sets'

    def save(self, *args, **kwargs):
        # If this instance is being activated, ensure all others are deactivated
        if self.active:
            # Use update to avoid saving each instance individually
            type(self).objects.exclude(pk=self.pk).update(active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.date})"


class SetSong(models.Model):
    set = models.ForeignKey(Set, on_delete=models.CASCADE)
    song = models.ForeignKey('songs.Song', on_delete=models.CASCADE)
    order = models.IntegerField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    # Mark which song in the set is currently active (only one per set)
    active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('set', 'song')
        ordering = ['order']

    def save(self, *args, **kwargs):
        # If this SetSong is being activated, deactivate others in the same set
        if self.active:
            type(self).objects.filter(set=self.set).exclude(pk=self.pk).update(active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.set} - {self.song} (order={self.order}, active={self.active})"

