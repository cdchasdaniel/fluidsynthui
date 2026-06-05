# FluidSynthUI

A Django-based web application for managing MIDI patches, songs, and performance sets using FluidSynth sound synthesis.

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
- **Song Organization**: Associate songs with patches, store notes and tempo information
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

### FluidSynth Settings

All FluidSynth audio and MIDI settings are configured in `fluidsynth.cfg` in the project root. This file is read when the application starts.

**Example configuration:**
```ini
# FluidSynth Configuration File
soundfont_path = sf
audio.driver = alsa
audio.period-size = 64
audio.periods = 2
audio.realtime-prio = 70
midi.autoconnect = 1
```

**Key settings:**
- `soundfont_path`: Path to the directory containing SoundFont files (can be relative to project root or absolute)
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
├── cfluid/                # C extension for FluidSynth
├── sf/                    # SoundFont files (.sf2)
├── static/                # Static files (CSS, JS)
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
3. Enter song details (name, notes, tempo)
4. Associate with a patch

### Creating a Set

1. Navigate to the Sets section
2. Click "Add Set"
3. Enter set details (name, date, location, description)
4. Add and order songs for the performance
5. Mark as active to use for current performance

## API

FluidSynthUI exposes a REST API that allows external devices (such as Stream Deck, tablets, or control surfaces) to control the playback and navigation of sets and songs.

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
   - For local network usage, endpoints may work without authentication
   - For remote access, configure authentication headers as needed

### Response Format

Endpoints return JSON with the current song information:
```json
{
  "success": true,
  "current_song": "Song Name",
  "song_index": 1,
  "total_songs": 10,
  "set_name": "Active Set Name"
}
```


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
- Song metadata (name, notes, tempo)
- Associated with a patch

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

