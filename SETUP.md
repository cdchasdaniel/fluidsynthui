# SETUP — FluidSynth & C extension

This file documents the commands to install FluidSynth development headers, verify `pkg-config`, and build the native libraries used by this project.

1) Install FluidSynth development files and build tools.

Debian/Ubuntu / Raspberry Pi OS:

```bash
sudo apt update
sudo apt install -y pkg-config libfluidsynth-dev mpg123 build-essential
```

`mpg123` is required at runtime for MP3 trigger playback on Linux (CC16-CC23).

macOS with Homebrew:

```bash
xcode-select --install
brew install fluid-synth pkg-config
```

MP3 playback on macOS uses the built-in `afplay` command, so `mpg123` is not required there.

2) Verify `pkg-config` sees FluidSynth:

```bash
pkg-config --modversion fluidsynth
pkg-config --cflags --libs fluidsynth
```

3) Build all native libraries from the project root:

```bash
make -C cfluid all
```

This builds `libcfluid.so` (main synth), `libmetronome.so`, and `libpad.so`. The Django
application needs all three for the main synth, metronome, and chord-pad features. To build
only one library, run `make -C cfluid lib`, `make -C cfluid metronome`, or
`make -C cfluid pad`.

4) If FluidSynth was installed to a non-standard prefix and `pkg-config` can't find it, set
the appropriate paths before building. For example, on Linux with a `/usr/local` install:

```bash
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
make -C cfluid all
```

On macOS with Homebrew, Homebrew usually configures `pkg-config` automatically. If needed,
use `brew --prefix fluid-synth` to find its prefix, add its `lib/pkgconfig` directory to
`PKG_CONFIG_PATH`, and its `lib` directory to `DYLD_LIBRARY_PATH`.

5) If you cannot install via a package manager or need a newer FluidSynth, build from source — follow the FluidSynth project instructions. A typical Linux build uses Meson/Ninja, for example:

```bash
git clone https://github.com/FluidSynth/fluidsynth.git
cd fluidsynth
# follow upstream build instructions; example (may vary by version):
meson setup build
meson compile -C build
sudo meson install -C build
sudo ldconfig
```

After installing development headers from source, re-run the `pkg-config` checks and then
run `make -C cfluid all` from the project root.

## MP3 upload configuration

MP3 uploads are stored in `media/mp3/`, which the application creates as needed. Set
`mp3_max_upload_mb` in the active root-level `fluidsynth.cfg` to control the per-file upload
limit, for example:

```ini
mp3_max_upload_mb = 100
```

When switching systems, copy the desired platform config (for example,
`fluidsynth mac.cfg` or `fluidsynth_raspberry_pi.cfg`) to `fluidsynth.cfg` and retain this
setting. On Linux, install `mpg123` for playback; macOS uses `afplay`.


## Note about Django dev-server autoreloader

The Django development server uses an autoreloader that starts the process twice (a monitor and a worker). Initializing FluidSynth at import time can cause the audio device to be opened twice and lead to errors like:

```
fluidsynth: error: The "default" audio device is used by another application
```

`SongsConfig.ready()` initializes the metronome and pad managers in each Django process; it
does not guard against the autoreloader's monitor/worker processes. Disable the autoreloader
when running the development server so the audio devices are initialized only once:

```bash
python manage.py runserver --noreload 0.0.0.0:8080
```

If you plan to run in production with a multi-worker server (e.g. Gunicorn), run FluidSynth as a separate service or ensure only a single dedicated process opens the audio device. I can help add a systemd service or a tiny IPC wrapper if you'd like.
