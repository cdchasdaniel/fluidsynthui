# SETUP — Raspberry Pi (FluidSynth, C extension & Bitfocus Companion)

This file covers installing FluidSynth development headers, verifying `pkg-config`, building the native libraries, and installing Bitfocus Companion on a Raspberry Pi. For macOS, see [SETUP_MAC.md](SETUP_MAC.md). To run the app at boot, see [AUTOSTART.md](AUTOSTART.md).

## 1) Install FluidSynth development files and build tools

Raspberry Pi OS / Debian / Ubuntu:

```bash
sudo apt update
sudo apt install -y pkg-config libfluidsynth-dev mpg123 build-essential
```

- `pkg-config` tells the compiler where FluidSynth's headers and link flags are.
- `libfluidsynth-dev` provides the FluidSynth headers and pulls in the runtime library.
- `mpg123` is required at runtime for MP3 playback.
- `build-essential` provides `gcc`, `make`, and libc headers.

## 2) Verify `pkg-config` sees FluidSynth

```bash
pkg-config --modversion fluidsynth
pkg-config --cflags --libs fluidsynth
```

## 3) Build all native libraries from the project root

```bash
make -C cfluid all
```

This builds `libcfluid.so` (main synth), `libmetronome.so`, and `libpad.so`. The Django
application needs all three. To build only one, run `make -C cfluid lib`,
`make -C cfluid metronome`, or `make -C cfluid pad`.

## 4) Non-standard FluidSynth prefix

If FluidSynth was installed to a non-standard prefix and `pkg-config` can't find it:

```bash
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
make -C cfluid all
```

## 5) Build FluidSynth from source (if needed)

If you need a newer FluidSynth than the package manager provides, follow the FluidSynth
project instructions. A typical build uses Meson/Ninja:

```bash
git clone https://github.com/FluidSynth/fluidsynth.git
cd fluidsynth
meson setup build
meson compile -C build
sudo meson install -C build
sudo ldconfig
```

Then re-run the `pkg-config` checks and `make -C cfluid all`.

## Bitfocus Companion

Bitfocus Companion is an essential part of the system: it drives the Stream Deck and sends the
HTTP requests (next/previous song, MP3 play/stop, service start/stop) to FluidSynthUI. Install
it with the official installer:

```bash
curl https://raw.githubusercontent.com/bitfocus/companion-pi/main/install.sh | bash
```

The installer sets Companion up as its own systemd service that starts at boot. Its admin UI
is at `http://<pi-ip>:8000`, separate from FluidSynthUI (port 8080) and the control daemon
(port 8081). It is not managed by the unit files in `.config/systemd/user/`. See the
[API section of the README](README.md#api) for the endpoints to call from Companion buttons.

## MP3 upload configuration

MP3 uploads are stored in `media/mp3/`, which the application creates as needed. Set
`mp3_max_upload_mb` in the root-level `fluidsynth.cfg` to control the per-file upload limit:

```ini
mp3_max_upload_mb = 100
```

Copy `fluidsynth_raspberry_pi.cfg` to `fluidsynth.cfg` and retain this setting.

## Django dev-server autoreloader

The Django development server's autoreloader starts the process twice (a monitor and a worker),
which can open the audio device twice and cause errors like:

```
fluidsynth: error: The "default" audio device is used by another application
```

Disable the autoreloader so the audio devices are initialized only once:

```bash
python manage.py runserver --noreload 0.0.0.0:8080
```

If you run in production with a multi-worker server (e.g. Gunicorn), run FluidSynth as a
separate service or ensure only one dedicated process opens the audio device.
