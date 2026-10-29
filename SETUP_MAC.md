# SETUP — macOS (FluidSynth & C extension)

This file covers installing FluidSynth, verifying `pkg-config`, and building the native libraries on macOS. For Raspberry Pi, see [SETUP_RASPBERRY_PI.md](SETUP_RASPBERRY_PI.md).

## 1) Install FluidSynth and build tools

```bash
xcode-select --install
brew install fluid-synth pkg-config
```

- `xcode-select --install` provides the C compiler and `make`.
- `fluid-synth` installs the FluidSynth library and headers.
- `pkg-config` tells the compiler where FluidSynth's headers and link flags are.

MP3 playback uses the built-in `afplay` command, so `mpg123` is not required.

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

Homebrew usually configures `pkg-config` automatically. If it can't find FluidSynth, use
`brew --prefix fluid-synth` to find the prefix, add its `lib/pkgconfig` directory to
`PKG_CONFIG_PATH`, and its `lib` directory to `DYLD_LIBRARY_PATH`.

## MP3 upload configuration

MP3 uploads are stored in `media/mp3/`, which the application creates as needed. Set
`mp3_max_upload_mb` in the root-level `fluidsynth.cfg` to control the per-file upload limit:

```ini
mp3_max_upload_mb = 100
```

Copy `fluidsynth mac.cfg` to `fluidsynth.cfg` and retain this setting.

## Bitfocus Companion

If you use a Stream Deck on the Mac, install Bitfocus Companion from
<https://bitfocus.io/companion> (download the macOS app). Its admin UI runs on port 8000.
See the [API section of the README](README.md#api) for the endpoints to call from buttons.

## Django dev-server autoreloader

The Django development server's autoreloader starts the process twice, which can open the audio
device twice. Disable it so the audio devices are initialized only once:

```bash
python manage.py runserver --noreload 0.0.0.0:8080
```
