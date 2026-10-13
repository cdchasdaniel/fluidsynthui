# SETUP — FluidSynth & C extension

This file documents the commands to install FluidSynth development headers, verify `pkg-config`, and build the `cfluid` C extension used by this project.

1) Install FluidSynth dev headers, `mpg123` runtime, and build tools (Debian/Ubuntu / Raspberry Pi OS):

```bash
sudo apt update
sudo apt install -y pkg-config libfluidsynth-dev mpg123 build-essential
```

`mpg123` is required at runtime for MP3 trigger playback on Linux (CC16-CC23).

2) Verify `pkg-config` sees FluidSynth:

```bash
pkg-config --modversion fluidsynth
pkg-config --cflags --libs fluidsynth
```

3) Build the C extension in this repo:

```bash
cd cfluid
make lib
```

This builds only `libcfluid.so` (the main synth engine). The metronome and chord/pad
features load their own separate FluidSynth instances from `libmetronome.so` and
`libpad.so`. Build everything at once with:

```bash
cd cfluid
make all
```

or build them individually with `make metronome` / `make pad`.

4) If FluidSynth was installed to a non-standard prefix (for example `/usr/local`) and `pkg-config` can't find it, set these env vars before building:

```bash
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
make lib
```

5) If you cannot install via `apt` or need a newer FluidSynth, build from source — follow the FluidSynth project instructions. A typical build uses Meson/Ninja, for example:

```bash
git clone https://github.com/FluidSynth/fluidsynth.git
cd fluidsynth
# follow upstream build instructions; example (may vary by version):
meson setup build
meson compile -C build
sudo meson install -C build
sudo ldconfig
```

After installing development headers from source, re-run the `pkg-config` checks and then `make lib` in `cfluid`.


## Note about Django dev-server autoreloader

The Django development server uses an autoreloader that starts the process twice (a monitor and a worker). Initializing FluidSynth at import time can cause the audio device to be opened twice and lead to errors like:

```
fluidsynth: error: The "default" audio device is used by another application
```

To avoid this during development, run the server normally (the codebase guards initialization), or disable the autoreloader for debugging:

```bash
python manage.py runserver --noreload 0.0.0.0:8080
```

If you plan to run in production with a multi-worker server (e.g. Gunicorn), run FluidSynth as a separate service or ensure only a single dedicated process opens the audio device. I can help add a systemd service or a tiny IPC wrapper if you'd like.
