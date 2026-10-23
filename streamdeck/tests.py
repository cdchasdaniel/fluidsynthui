from django.test import TestCase
from django.urls import reverse

from set.models import Set, SetSong
from songs.models import Song


class StreamDeckTests(TestCase):
    def test_stream_deck_is_outside_sets_and_shows_active_song_slots(self):
        song = Song.objects.create(name='Opening', mp3_slot_1='intro.mp3')
        active_set = Set.objects.create(name='Tonight', active=True)
        SetSong.objects.create(set=active_set, song=song, active=True)

        response = self.client.get(reverse('stream_deck'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Opening')
        self.assertContains(response, 'intro.mp3')
        self.assertContains(response, reverse('mp3_play_slot', args=[1]))