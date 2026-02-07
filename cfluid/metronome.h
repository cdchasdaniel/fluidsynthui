#ifndef METRONOME_H
#define METRONOME_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int bpm;
    int beats_per_measure;
    int note_value;  /* denominator of time signature (e.g., 4 for 4/4) */
    int accent_note;  /* MIDI note for accent beat */
    int normal_note;  /* MIDI note for normal beat */
    int channel;      /* MIDI channel (0-based) */
    int bank;         /* Bank number (e.g., 128 for drums) */
    int program;      /* Program/preset number (e.g., 16 for power drums) */
    int velocity;     /* Note velocity (0-127) */
    int duration_ms;  /* Note duration in milliseconds */
} metronome_config_t;

/**
 * Initialize the metronome with a separate fluidsynth instance
 * @param config_path Path to fluidsynth config file
 * @param soundfont_path Path to soundfont file (or NULL to use defaultGM.sf2)
 * @return 0 on success, -1 on failure
 */
int metronome_init(const char *config_path, const char *soundfont_path);

/**
 * Clean up metronome resources
 * @return 0 on success, -1 on failure
 */
int metronome_cleanup(void);

/**
 * Start the metronome
 * @param config Metronome configuration
 * @return 0 on success, -1 on failure
 */
int metronome_start(metronome_config_t *config);

/**
 * Stop the metronome
 * @return 0 on success, -1 on failure
 */
int metronome_stop(void);

/**
 * Check if metronome is running
 * @return 1 if running, 0 if stopped
 */
int metronome_is_running(void);

/**
 * Update metronome BPM (while running)
 * @param bpm New BPM value
 * @return 0 on success, -1 on failure
 */
int metronome_set_bpm(int bpm);

/**
 * Update metronome time signature (while running)
 * @param beats_per_measure Beats per measure
 * @param note_value Note value (denominator)
 * @return 0 on success, -1 on failure
 */
int metronome_set_time_signature(int beats_per_measure, int note_value);

#ifdef __cplusplus
}
#endif

#endif
