# FluidSynthUI

A Django-based web application for managing MIDI patches, songs, and performance sets using FluidSynth sound synthesis.

## YouTube
- [Part 1](https://youtu.be/ig6fRvsAYPI?si=8onGnVIzf6REO9Jp)
- [Part 2](https://youtu.be/oPLLUSc62pM?si=N85l4I37uh6Zoa8v)
- [Part 3](https://youtu.be/vLshE7TkruA?si=Cgnwa2B1qHX51vzj)
- [Part 4](https://youtu.be/xrrB5ETUj0c?si=21v9-DotUKOMFCYI)

## Overview

FluidSynthUI is a comprehensive system for organizing and managing MIDI performances. It provides a web interface for:
- Creating and managing multi-voice MIDI patches with reverb effects
- Organizing songs with their associated patches
- Building and managing performance sets (setlists)
- Real-time MIDI synthesis using FluidSynth with SoundFont support

Originally developed for running on a **Raspberry Pi connected to a Yamaha Keyboard** via USB MIDI, FluidSynthUI is designed to be lightweight and efficient. However, it supports any platform capable of running Python and FluidSynth, and works with a wide variety of MIDI devices and keyboards.

## Features

- **Patch Management**: Create complex multi-voice patches with individual settings per voice (volume, transpose, sustain, keyboard range)
- **Global Reverb Controls**: Configure reverb room size, damping, width, and level for each patch
- **Song Organization**: Associate songs with patches, store notes, tempo, and time signature
- **MP3 Library**: Upload and manage MP3 cues under `media/mp3`, then assign them to song buttons
- **Stream Deck Controls**: Use the `/stream-deck/` page or POST playback endpoints to control the active song's MP3 cues
- **Metronome**: Per-song tempo/time-signature metronome using a dedicated FluidSynth instance, controllable via start/stop/faster/slower/louder/softer endpoints
- **Chord Pads**: Sustained background chords (multiple notes from one soundfont/preset, with optional fade-in) that can be attached to a song and started/stopped/toggled independently of the main synth
- **Set/Setlist Management**: Build performance sets with ordered song lists and location tracking
- **SoundFont Support**: Use industry-standard SoundFont (.sf2) files for high-quality synthesis
- **Bootstrap UI**: Modern, responsive interface using Bootstrap 5
- **C Extension**: Custom FluidSynth integration for efficient audio synthesis

## Requirements

- Python 3.8+
- FluidSynth library
- `mpg123` (Linux runtime dependency for MP3 trigger playback)
- SQLite (included with Python)
- SoundFont files (.sf2)
- C compiler (gcc, clang, or MSVC) - only needed if compiling the C extension

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cdchasdaniel/fluidsynthui.git
   cd fluidsynthui
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FluidSynth:**
   - macOS: `brew install fluid-synth`
   - Linux: `apt-get install fluidsynth mpg123` or `yum install fluidsynth mpg123`
   - Windows: Download from [FluidSynth website](https://www.fluidsynth.org/)

For detailed FluidSynth and C-extension setup (installing development headers, pkg-config checks, and building the `cfluid` library), see [SETUP.md](SETUP.md).

5. **Compile the C extension (optional):**
   ```bash
   cd cfluid
   make
   cd ..
   ```

6. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

7. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

9. **Access the application:**
   - Web interface: http://127.0.0.1:8000
   - Admin interface: http://127.0.0.1:8000/admin

## Configuration

### FluidSynth and MP3 Settings

FluidSynth audio and MIDI settings, plus the MP3 upload size limit, are configured in `fluidsynth.cfg` in the project root. This file is read when the application starts. The platform-specific examples `fluidsynth mac.cfg` and `fluidsynth_raspberry_pi.cfg` also include the upload limit; copy/rename the appropriate file to `fluidsynth.cfg` for the current system.

**Example configuration:**
```ini
# FluidSynth Configuration File
soundfont_path = sf
mp3_max_upload_mb = 100
audio.driver = alsa
audio.period-size = 64
audio.periods = 2
audio.realtime-prio = 70
midi.autoconnect = 1
```

**Key settings:**
- `soundfont_path`: Path to the directory containing SoundFont files (can be relative to project root or absolute)
- `mp3_max_upload_mb`: Maximum upload size for an MP3 file, in megabytes
- `audio.driver`: Audio backend (alsa, pulseaudio, jack, oss, etc.)
- `audio.period-size`: Buffer size in frames (lower = less latency, more CPU)
- `audio.periods`: Number of audio periods (2-16)
- `audio.realtime-prio`: Real-time priority (0-99, 0 = disabled)
- `midi.autoconnect`: Auto-connect MIDI devices (0 or 1)

For a complete list of available settings, see the [FluidSynth documentation](https://www.fluidsynth.org/api/fluidsettings.xml).

### Django Settings

Edit `fluidsynthui/settings.py` to configure:
- `ALLOWED_HOSTS`: Add your server IP addresses
- `CSRF_TRUSTED_ORIGINS`: Add trusted origins for CSRF protection
- `SECRET_KEY`: Change in production

### SoundFonts

**Important:** The `sf/` directory is not included in the repository due to GitHub file size limitations. You must create this directory and add SoundFont files manually.

1. **Create the SoundFonts directory:**
   ```bash
   mkdir -p sf
   ```

2. **Add SoundFont files:** Download and place `.sf2` files in the `sf/` directory. Some popular options:
   - [FluidR3_GM.sf2](https://sourceforge.net/projects/fluidsynth-soundfont/files/release/) - General MIDI SoundFont
   - [TimGM6mb.sf2](https://www.freepats.zenvoid.org/Piano/acoustic-grand-piano.html) - Compact GM SoundFont
   - Other SoundFonts from [Freepats](https://www.freepats.zenvoid.org/) or [MuseScore](https://musescore.org/en/handbook/3/soundfonts-and-sfz-files)

The application will use any `.sf2` files found in this directory.

## Project Structure

```
fluidsynthui/              # Main Django project directory
├── fluidsynthui/          # Core Django configuration
│   ├── settings.py        # Project settings
│   ├── urls.py            # URL routing
│   ├── wsgi.py            # WSGI application
│   └── asgi.py            # ASGI application
├── patches/               # Patch and voice management app
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── migrations/
├── songs/                 # Song management app
│   ├── models.py
│   ├── views.py
│   └── migrations/
├── set/                   # Setlist management app
│   ├── models.py
│   ├── views.py
│   └── migrations/
├── pads/                  # Chord/pad management app
│   ├── models.py
│   ├── views.py
│   └── migrations/
├── mp3/                   # MP3 library, upload/delete, and playback API
├── streamdeck/            # Stream Deck controller page
├── cfluid/                # C extension for FluidSynth
├── sf/                    # SoundFont files (.sf2)
├── static/                # Static files (CSS, JS)
├── media/mp3/              # Uploaded MP3 files (created as needed)
├── templates/             # HTML templates
├── poc/                   # Proof-of-concept scripts
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## Usage

### Creating a Patch

1. Navigate to the Patches section
2. Click "Add Patch" and enter a name
3. Configure global reverb settings
4. Add voices to the patch:
   - Select SoundFont file
   - Choose preset (instrument)
   - Set volume, transpose, and keyboard range
   - Enable/disable sustain pedal response

### Creating a Song

1. Navigate to the Songs section
2. Click "Add Song"
3. Enter song details (name, notes, tempo, time signature)
4. Associate with a patch
5. Optionally associate a chord Pad and/or assign files from the MP3 Library to the 8 MP3 slots

### Managing MP3 Cues

1. Open **MP3 Library** from the navigation or home page.
2. Upload `.mp3` files. Uploads are stored in `media/mp3/`; the maximum size is set by `mp3_max_upload_mb` in `fluidsynth.cfg`.
3. Assign files to the song's eight MP3 buttons in the Add/Edit Song form. Files assigned to songs cannot be deleted; the library reports which songs use them.
4. While that song is active, trigger a button with the Stream Deck page or the playback API below. Starting a cue stops any previously playing MP3 first.

### Using the Metronome and Chord Pads

While a set is active, the metronome and chord pad for the current song can be controlled via
the endpoints listed in the [API](#api) section below (e.g. from a Stream Deck or the
`/stream-deck/` page). The metronome uses the song's `tempo`/`time_signature`; the chord
pad plays whatever `Pad` is attached to the current song.

### Creating a Set

1. Navigate to the Sets section
2. Click "Add Set"
3. Enter set details (name, date, location, description)
4. Add and order songs for the performance
5. Mark as active to use for current performance

## API

FluidSynthUI exposes HTTP endpoints that allow external devices (such as Stream Deck, tablets, or control surfaces) to control playback and navigation of sets and songs.

### Previous/Next Endpoints

These endpoints control navigation through the active set's songs:

**Next Song**
```
GET /sets/active/song/next/activate/
```
Advances to the next song in the active set. If at the end of the setlist, loops back to the beginning.

**Previous Song**
```
GET /sets/active/song/prev/activate/
```
Goes to the previous song in the active set. If at the beginning, loops to the end of the setlist.

### Example Usage with Stream Deck

You can use these endpoints with external control devices:

1. **Stream Deck Integration:**
   - Add custom URL action to Stream Deck
   - On button press: `http://your-server:8000/sets/active/song/next/activate/`
   - On button press: `http://your-server:8000/sets/active/song/prev/activate/`

2. **Curl Examples:**
   ```bash
   # Advance to next song
   curl http://127.0.0.1:8000/sets/active/song/next/activate/

   # Go to previous song
   curl http://127.0.0.1:8000/sets/active/song/prev/activate/
   ```

3. **Authentication:**
   - The control endpoints do not currently implement authentication
   - Keep access limited to a trusted local network; authentication headers are not supported

### Response Format

Endpoints return JSON describing the newly active song:
```json
{
  "song": {"id": 12, "name": "Song Name"},
  "current_song_name": "Song Name"
}
```
If there is no next/previous song (end/start of the setlist) or no active set, `song` and
`current_song_name` are `null`, or an `error` key is returned (e.g. `{"error": "No active set"}`).

### Other Control Endpoints

These additional fixed URLs are also designed for external control surfaces (e.g. Stream Deck):

| Endpoint | Purpose |
|---|---|
| `GET/POST /sets/active/song/first/activate/` | Jump to the first song in the active set |
| `GET/POST /sets/active/song/last/activate/` | Jump to the last song in the active set |
| `GET /sets/active/song/current/` | Get the currently active song |
| `POST /sets/active/song/metronome/start/` | Start the metronome for the active song's tempo |
| `POST /sets/active/song/metronome/stop/` | Stop the metronome |
| `POST /sets/active/song/metronome/faster/` / `slower/` | Adjust metronome tempo |
| `POST /sets/active/song/metronome/louder/` / `softer/` | Adjust metronome volume |
| `POST /mp3/play/<slot>/` (`<slot>` is 1-8) | Play the active song's MP3 assigned to that button; stops any currently playing MP3 first |
| `POST /mp3/stop/` | Stop all MP3 playback |
| `GET/POST /sets/active/song/pad/start/` / `stop/` / `toggle/` | Control the active song's chord pad |
| `GET /stream-deck/` | Stream Deck page for song navigation, MP3 playback, metronome, and pad controls |

The MP3 playback endpoints are CSRF-exempt for hardware callers and do not currently require authentication. Use them only on a trusted network.

The standalone control daemon in [service_control.py](service_control.py) (listening on port
`8081` by default) exposes separate endpoints for starting/stopping the whole Django service
itself via `systemctl --user`:

```
GET http://127.0.0.1:8081/service/status/
GET http://127.0.0.1:8081/service/start/
GET http://127.0.0.1:8081/service/stop/
```

See [AUTOSTART.md](AUTOSTART.md) for setting this up as a systemd user service.


## Models

### Patch
- Multi-voice MIDI patch configuration
- Global reverb settings (room size, damping, width, level)
- Related voices with individual settings

### Voice
- Part of a patch
- SoundFont file and preset selection
- MIDI channel assignment
- Volume, transpose, sustain settings
- Keyboard range (low/high note)

### Song
- Song metadata (name, notes, tempo, time signature)
- Associated with a patch
- Optional associated Pad (sustained background chord)
- Up to 8 MP3 trigger slots (mapped to MIDI CC16-CC23), with files managed by the MP3 Library

### Pad
- A sustained chord: a soundfont/preset plus a list of MIDI note numbers
- Configurable velocity and fade-in duration
- Played through a separate FluidSynth instance managed by `PadManager` ([songs/pad_manager.py](songs/pad_manager.py))

### Set
- Performance setlist
- Contains ordered songs
- Location and date tracking
- Active set designation


### Database

The project uses SQLite by default. The database file is `db.sqlite3`.

### Admin Interface

Access the Django admin at `/admin` to manage all models directly.

## Troubleshooting

### FluidSynth not found
Make sure FluidSynth is installed and in your system PATH. You may need to install development headers:
- macOS: `brew install fluid-synth`
- Ubuntu: `apt-get install libfluidsynth-dev`

### Port already in use
Change the port when running the server:
```bash
python manage.py runserver 8001
```

