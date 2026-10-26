# Architecture Overview

```mermaid
flowchart TB
    subgraph Hardware["Stage hardware"]
        KB[MIDI keyboard]
        SD[Stream Deck / browser UI]
        SPK[Speakers / audio out]
    end

    subgraph Django["Django web app (Python)"]
        direction TB
        UI[Pages and JSON endpoints<br/>patches · songs · sets · pads · mp3 · streamdeck]
        DB[(SQLite<br/>patches, songs, sets,<br/>pads, MP3 assignments)]
        MGR[Managers stored in settings<br/>FLUID_SYNTH · METRONOME_MANAGER · PAD_MANAGER]
        UI <--> DB
        UI --> MGR
    end

    subgraph Native["Native C libraries, loaded via ctypes"]
        CF[libcfluid<br/>synth · MIDI routing · soundfonts · MP3 playback]
        MET[libmetronome]
        PAD[libpad]
    end

    CFG[[fluidsynth.cfg]]
    SF[(Soundfont .sf2 files)]
    MP3[(MP3 files)]
    FS[[FluidSynth engine]]
    AF[afplay / mpg123]

    SD -- HTTP --> UI
    KB -- MIDI --> FS
    MGR -- ctypes --> CF
    MGR -- ctypes --> MET
    MGR -- ctypes --> PAD
    CF --> FS
    MET --> FS
    PAD --> FS
    CFG --> CF
    CFG --> MET
    CFG --> PAD
    SF --> CF
    MP3 --> UI
    CF -- spawns --> AF
    FS --> SPK
    AF --> SPK
```

## How it fits together

- **Control:** The Stream Deck or browser sends HTTP requests to Django. Activating a song or set looks up its patch in SQLite and applies it to the synth.
- **Bridge:** Django starts three managers at launch and stores them in settings. Each manager wraps a native C library through `ctypes`.
- **Audio:** FluidSynth turns the keyboard's MIDI input into sound using the loaded soundfonts. The metronome and pad libraries drive the same engine. MP3s play as a separate `afplay`/`mpg123` process.
- **Configuration:** All three C libraries read the same `fluidsynth.cfg`.
