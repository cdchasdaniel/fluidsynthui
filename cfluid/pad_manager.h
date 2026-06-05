#ifndef PAD_MANAGER_H
#define PAD_MANAGER_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int bpm;           /* BPM (for potential arpeggio/rhythm features) */
    int *notes;        /* Array of MIDI note numbers */
    int note_count;    /* Number of notes in the chord */
    int velocity;      /* Note velocity (0-127) */
    int sustain;       /* 1 if notes should sustain indefinitely, 0 if one-shot */
    int duration_ms;   /* If sustain=0, hold for this many ms */
    int fade_in_ms;    /* Fade in duration in milliseconds (0 = instant) */
} pad_config_t;

/**
 * Initialize the pad manager with a separate fluidsynth instance
 * @param config_path Path to fluidsynth config file
 * @param soundfont_path Path to soundfont file (or NULL to use defaultGM.sf2)
 * @return 0 on success, -1 on failure
 */
int pad_manager_init(const char *config_path, const char *soundfont_path);

/**
 * Clean up pad manager resources
 * @return 0 on success, -1 on failure
 */
int pad_manager_cleanup(void);

/**
 * Start playing a pad (chord)
 * @param config Pad configuration
 * @param soundfont_name Name of soundfont to use (e.g., "defaultGM.sf2")
 * @param preset Preset string in format "bank:program" (e.g., "000:000")
 * @return 0 on success, -1 on failure
 */
int pad_start(pad_config_t *config, const char *soundfont_name, const char *preset);

/**
 * Stop playing the current pad
 * @return 0 on success, -1 on failure
 */
int pad_stop(void);

/**
 * Check if pad is currently playing
 * @return 1 if playing, 0 if stopped
 */
int pad_is_playing(void);

#ifdef __cplusplus
}
#endif

#endif
