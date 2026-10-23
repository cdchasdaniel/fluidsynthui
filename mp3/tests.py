from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from set.models import Set, SetSong
from songs.models import Song


class Mp3LibraryTests(TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.media_root = self.root / 'media'
        self.settings_override = override_settings(BASE_DIR=self.root, MEDIA_ROOT=self.media_root)
        self.settings_override.enable()
        (self.root / 'fluidsynth.cfg').write_text('mp3_max_upload_mb = 1\n', encoding='utf-8')

    def tearDown(self):
        self.settings_override.disable()
        self.temp_dir.cleanup()

    def upload(self, name, content=b'mp3-data'):
        return self.client.post(reverse('mp3_upload'), {
            'file': SimpleUploadedFile(name, content),
        }, follow=True)

    def test_upload_accepts_mp3_and_rejects_duplicate_case_insensitively(self):
        response = self.upload('Backing Track.MP3')
        self.assertTrue((self.media_root / 'mp3' / 'Backing Track.MP3').is_file())
        self.assertContains(response, 'Uploaded')

        response = self.upload('backing track.mp3')
        self.assertContains(response, 'already exists')
        self.assertEqual(
            sum(path.is_file() and path.suffix.lower() == '.mp3' for path in (self.media_root / 'mp3').iterdir()),
            1,
        )

    def test_upload_rejects_non_mp3_and_oversized_file(self):
        response = self.upload('track.wav')
        self.assertContains(response, 'Only .mp3 files')

        response = self.upload('large.mp3', b'x' * (1024 * 1024 + 1))
        self.assertContains(response, '1 MB upload limit')
        self.assertFalse((self.media_root / 'mp3' / 'large.mp3').exists())

    def test_delete_is_blocked_when_a_song_uses_the_file(self):
        directory = self.media_root / 'mp3'
        directory.mkdir(parents=True)
        (directory / 'cue.mp3').write_bytes(b'audio')
        song = Song.objects.create(name='Opening', mp3_slot_1='cue.mp3')

        response = self.client.post(reverse('mp3_delete'), {'filename': 'cue.mp3'}, follow=True)

        self.assertContains(response, 'Opening')
        self.assertTrue((directory / 'cue.mp3').exists())
        song.mp3_slot_1 = None
        song.save()
        self.client.post(reverse('mp3_delete'), {'filename': 'cue.mp3'})
        self.assertFalse((directory / 'cue.mp3').exists())

    def test_legacy_static_mp3s_are_copied_to_media_directory(self):
        legacy_directory = self.root / 'static' / 'mp3'
        legacy_directory.mkdir(parents=True)
        (legacy_directory / 'legacy.mp3').write_bytes(b'legacy-audio')

        response = self.client.get(reverse('mp3_library'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual((self.media_root / 'mp3' / 'legacy.mp3').read_bytes(), b'legacy-audio')

    @patch('mp3.views.play_mp3_file', return_value=0)
    @patch('mp3.views.stop_mp3_playback', return_value=0)
    def test_play_service_stops_previous_audio_then_plays_active_song_slot(self, stop_audio, play_audio):
        directory = self.media_root / 'mp3'
        directory.mkdir(parents=True)
        audio_path = directory / 'intro.mp3'
        audio_path.write_bytes(b'audio')
        song = Song.objects.create(name='Intro', mp3_slot_1='intro.mp3')
        active_set = Set.objects.create(name='Tonight', active=True)
        SetSong.objects.create(set=active_set, song=song, active=True)

        response = self.client.post(reverse('mp3_play_slot', args=[1]))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'slot': 1,
            'song': 'Intro',
            'file': 'intro.mp3',
        })
        stop_audio.assert_called_once_with(-1)
        play_audio.assert_called_once_with(str(audio_path).encode('utf-8'), 0)

    @patch('mp3.views.stop_mp3_playback', return_value=0)
    def test_stop_service_stops_all_slots(self, stop_audio):
        response = self.client.post(reverse('mp3_stop'))

        self.assertEqual(response.status_code, 200)
        stop_audio.assert_called_once_with(-1)