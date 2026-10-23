import shutil
from pathlib import Path

from django.conf import settings


DEFAULT_MAX_UPLOAD_MB = 100
MAX_UPLOAD_CONFIG_KEY = 'mp3_max_upload_mb'


def get_mp3_directory():
    directory = Path(settings.MEDIA_ROOT) / 'mp3'
    directory.mkdir(parents=True, exist_ok=True)
    _import_legacy_files(directory)
    return directory


def get_max_upload_mb():
    config_path = Path(settings.BASE_DIR) / 'fluidsynth.cfg'
    try:
        for line in config_path.read_text(encoding='utf-8').splitlines():
            entry = line.split('#', 1)[0]
            if '=' not in entry:
                continue
            key, value = (part.strip() for part in entry.split('=', 1))
            if key == MAX_UPLOAD_CONFIG_KEY:
                max_mb = int(value)
                return max_mb if max_mb > 0 else DEFAULT_MAX_UPLOAD_MB
    except (OSError, ValueError):
        pass
    return DEFAULT_MAX_UPLOAD_MB


def find_song_references(filename):
    from songs.models import Song

    matching_songs = []
    target = filename.casefold()
    slot_fields = [f'mp3_slot_{slot}' for slot in range(1, 9)]
    for song in Song.objects.only('name', *slot_fields):
        if any((getattr(song, field) or '').casefold() == target for field in slot_fields):
            matching_songs.append(song)
    return matching_songs


def _import_legacy_files(destination):
    """Copy bundled static MP3s once so existing song assignments keep working."""
    marker = destination / '.legacy_static_mp3_imported'
    if marker.exists():
        return

    legacy_directory = Path(settings.BASE_DIR) / 'static' / 'mp3'
    existing_names = {
        path.name.casefold()
        for path in destination.iterdir()
        if path.is_file() and path.suffix.lower() == '.mp3'
    }
    if legacy_directory.is_dir():
        for source in legacy_directory.iterdir():
            if not source.is_file() or source.suffix.lower() != '.mp3':
                continue
            if source.name.casefold() in existing_names:
                continue
            shutil.copy2(source, destination / source.name)
            existing_names.add(source.name.casefold())

    marker.touch()