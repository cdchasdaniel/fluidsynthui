#include <fluidsynth.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include "metronome.h"
#include "config.h"

/* Global metronome state */
static struct {
    fluid_settings_t *settings;
    fluid_synth_t *synth;
    fluid_audio_driver_t *adriver;
    int sfont_id;
    int is_running;
    int is_initialized;
    pthread_t thread;
    pthread_mutex_t mutex;
    metronome_config_t config;
} g_metronome = {
    .settings = NULL,
    .synth = NULL,
    .adriver = NULL,
    .sfont_id = -1,
    .is_running = 0,
    .is_initialized = 0,
    .thread = 0,
    .config = {0}
};

static void* metronome_thread_func(void *arg);
static long get_time_ms(void);
static void play_note(int note, int velocity, int duration_ms);

int metronome_init(const char *config_path, const char *soundfont_path)
{
    if (g_metronome.is_initialized) {
        fprintf(stderr, "Metronome already initialized\n");
        return 0;
    }

    char sf_dir[512] = {0};
    char sf_dir_temp[512] = {0};
    char config_dir[512];
    config_t config = {0};

    pthread_mutex_init(&g_metronome.mutex, NULL);

    /* Parse config file */
    if (config_path == NULL || config_path[0] == '\0') {
        printf("Warning: config_path cannot be empty, using defaults\n");
        strcpy(sf_dir, "sf");
    } else {
        if (!parse_config_file(config_path, &config, sf_dir_temp)) {
            printf("Warning: Failed to parse config file, using defaults\n");
            strcpy(sf_dir, "sf");
        } else {
            /* Get the directory containing the config file */
            strncpy(config_dir, config_path, sizeof(config_dir) - 1);
            config_dir[sizeof(config_dir) - 1] = '\0';
            char *last_slash = strrchr(config_dir, '/');
            if (last_slash != NULL) {
                *last_slash = '\0';
            } else {
                config_dir[0] = '.';
                config_dir[1] = '\0';
            }

            printf("Config directory: %s\n", config_dir);
            printf("Soundfont path from config: %s\n", sf_dir_temp[0] ? sf_dir_temp : "(empty)");

            if (sf_dir_temp[0] == '\0') {
                snprintf(sf_dir, sizeof(sf_dir), "%s/sf", config_dir);
            } else if (sf_dir_temp[0] == '/') {
                strncpy(sf_dir, sf_dir_temp, sizeof(sf_dir) - 1);
                sf_dir[sizeof(sf_dir) - 1] = '\0';
            } else {
                snprintf(sf_dir, sizeof(sf_dir), "%s/%s", config_dir, sf_dir_temp);
            }
        }
    }

    printf("Final soundfont directory: %s\n", sf_dir);

    /* Create the settings. */
    g_metronome.settings = new_fluid_settings();
    if (g_metronome.settings == NULL) {
        puts("Failed to create the settings!");
        return -1;
    }

    /* Apply settings from config file */
    for (int i = 0; i < config.count; i++) {
        const char *key = config.keys[i];
        const char *value = config.values[i];

        if (key == NULL || value == NULL) continue;

        /* Skip soundfont_path as we handle it separately */
        if (strcmp(key, "soundfont_path") == 0) continue;

        printf("Applying setting: %s = %s\n", key, value);
        fluid_settings_setstr(g_metronome.settings, key, value);
    }

    /* Create synth */
    g_metronome.synth = new_fluid_synth(g_metronome.settings);
    if (g_metronome.synth == NULL) {
        fprintf(stderr, "Failed to create fluidsynth instance\n");
        delete_fluid_settings(g_metronome.settings);
        g_metronome.settings = NULL;
        return -1;
    }

    /* Create audio driver */
    g_metronome.adriver = new_fluid_audio_driver(g_metronome.settings, g_metronome.synth);
    if (g_metronome.adriver == NULL) {
        fprintf(stderr, "Failed to create audio driver with configured settings\n");
        
        /* Try fallback: coreaudio on macOS, otherwise portaudio */
        #ifdef __APPLE__
        fprintf(stderr, "Trying coreaudio as fallback...\n");
        fluid_settings_setstr(g_metronome.settings, "audio.driver", "coreaudio");
        #else
        fprintf(stderr, "Trying portaudio as fallback...\n");
        fluid_settings_setstr(g_metronome.settings, "audio.driver", "portaudio");
        #endif
        
        g_metronome.adriver = new_fluid_audio_driver(g_metronome.settings, g_metronome.synth);
        if (g_metronome.adriver == NULL) {
            fprintf(stderr, "Failed to create fallback audio driver\n");
            delete_fluid_synth(g_metronome.synth);
            delete_fluid_settings(g_metronome.settings);
            g_metronome.synth = NULL;
            g_metronome.settings = NULL;
            return -1;
        }
        printf("Successfully created fallback audio driver\n");
    }

    /* Load soundfont */
    char sf_path[512] = {0};
    if (soundfont_path == NULL || soundfont_path[0] == '\0') {
        snprintf(sf_path, sizeof(sf_path), "%s/defaultGM.sf2", sf_dir);
    } else {
        strncpy(sf_path, soundfont_path, sizeof(sf_path) - 1);
    }

    printf("Attempting to load soundfont from: %s\n", sf_path);
    g_metronome.sfont_id = fluid_synth_sfload(g_metronome.synth, sf_path, 1);
    if (g_metronome.sfont_id == -1) {
        fprintf(stderr, "Failed to load soundfont: %s\n", sf_path);
        fprintf(stderr, "Metronome may not produce sound without a soundfont loaded\n");
    } else {
        printf("Loaded soundfont: %s (id=%d)\n", sf_path, g_metronome.sfont_id);
        /* Select instrument on channel 0 - bank 0, program 0 (acoustic piano) */
        fluid_synth_bank_select(g_metronome.synth, 0, 0);
        fluid_synth_program_change(g_metronome.synth, 0, 0);
        printf("Set channel 0 to bank 0, program 0\n");
    }

    g_metronome.is_initialized = 1;
    printf("Metronome initialized successfully\n");
    return 0;
}

int metronome_cleanup(void)
{
    if (!g_metronome.is_initialized) {
        return 0;
    }

    metronome_stop();

    pthread_mutex_lock(&g_metronome.mutex);

    if (g_metronome.adriver != NULL) {
        delete_fluid_audio_driver(g_metronome.adriver);
        g_metronome.adriver = NULL;
    }

    if (g_metronome.synth != NULL) {
        delete_fluid_synth(g_metronome.synth);
        g_metronome.synth = NULL;
    }

    if (g_metronome.settings != NULL) {
        delete_fluid_settings(g_metronome.settings);
        g_metronome.settings = NULL;
    }

    g_metronome.is_initialized = 0;
    g_metronome.sfont_id = -1;

    pthread_mutex_unlock(&g_metronome.mutex);
    pthread_mutex_destroy(&g_metronome.mutex);

    printf("Metronome cleaned up\n");
    return 0;
}

int metronome_start(metronome_config_t *config)
{
    if (!g_metronome.is_initialized) {
        fprintf(stderr, "Metronome not initialized\n");
        return -1;
    }

    if (g_metronome.is_running) {
        fprintf(stderr, "Metronome already running\n");
        return -1;
    }

    if (config == NULL) {
        fprintf(stderr, "Invalid config\n");
        return -1;
    }

    pthread_mutex_lock(&g_metronome.mutex);
    memcpy(&g_metronome.config, config, sizeof(metronome_config_t));
    g_metronome.is_running = 1;
    pthread_mutex_unlock(&g_metronome.mutex);

    if (pthread_create(&g_metronome.thread, NULL, metronome_thread_func, NULL) != 0) {
        fprintf(stderr, "Failed to create metronome thread\n");
        pthread_mutex_lock(&g_metronome.mutex);
        g_metronome.is_running = 0;
        pthread_mutex_unlock(&g_metronome.mutex);
        return -1;
    }

    printf("Metronome started: BPM=%d, Time Signature=%d/%d, Bank=%d, Program=%d\n",
           config->bpm, config->beats_per_measure, config->note_value,
           config->bank, config->program);
    return 0;
}

int metronome_stop(void)
{
    if (!g_metronome.is_running) {
        return 0;
    }

    pthread_mutex_lock(&g_metronome.mutex);
    g_metronome.is_running = 0;
    pthread_mutex_unlock(&g_metronome.mutex);

    if (g_metronome.thread != 0) {
        pthread_join(g_metronome.thread, NULL);
        g_metronome.thread = 0;
    }

    printf("Metronome stopped\n");
    return 0;
}

int metronome_is_running(void)
{
    int running;
    pthread_mutex_lock(&g_metronome.mutex);
    running = g_metronome.is_running;
    pthread_mutex_unlock(&g_metronome.mutex);
    return running;
}

int metronome_set_bpm(int bpm)
{
    if (bpm <= 0 || bpm > 300) {
        fprintf(stderr, "Invalid BPM: %d\n", bpm);
        return -1;
    }

    pthread_mutex_lock(&g_metronome.mutex);
    g_metronome.config.bpm = bpm;
    pthread_mutex_unlock(&g_metronome.mutex);

    printf("BPM updated to %d\n", bpm);
    return 0;
}

int metronome_set_time_signature(int beats_per_measure, int note_value)
{
    if (beats_per_measure <= 0 || beats_per_measure > 12) {
        fprintf(stderr, "Invalid beats per measure: %d\n", beats_per_measure);
        return -1;
    }

    if (note_value != 4 && note_value != 8 && note_value != 16) {
        fprintf(stderr, "Invalid note value: %d (must be 4, 8, or 16)\n", note_value);
        return -1;
    }

    pthread_mutex_lock(&g_metronome.mutex);
    g_metronome.config.beats_per_measure = beats_per_measure;
    g_metronome.config.note_value = note_value;
    pthread_mutex_unlock(&g_metronome.mutex);

    printf("Time signature updated to %d/%d\n", beats_per_measure, note_value);
    return 0;
}

/* Helper functions */

static long get_time_ms(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long)(ts.tv_sec * 1000 + ts.tv_nsec / 1000000);
}

static void play_note(int note, int velocity, int duration_ms)
{
    metronome_config_t config;
    pthread_mutex_lock(&g_metronome.mutex);
    memcpy(&config, &g_metronome.config, sizeof(metronome_config_t));
    pthread_mutex_unlock(&g_metronome.mutex);

    printf("  -> Playing note: %d, velocity: %d, channel: %d, bank: %d, program: %d, duration: %dms\n", 
           note, velocity, config.channel, config.bank, config.program, duration_ms);

    /* Set bank and program */
    int ret = fluid_synth_bank_select(g_metronome.synth, config.channel, config.bank);
    if (ret != FLUID_OK) {
        fprintf(stderr, "  ERROR: bank_select failed with code %d\n", ret);
    }
    
    ret = fluid_synth_program_change(g_metronome.synth, config.channel, config.program);
    if (ret != FLUID_OK) {
        fprintf(stderr, "  ERROR: program_change failed with code %d\n", ret);
    }

    /* Send note on */
    ret = fluid_synth_noteon(g_metronome.synth, config.channel, note, velocity);
    if (ret != FLUID_OK) {
        fprintf(stderr, "  ERROR: noteon failed with code %d\n", ret);
    }

    /* Sleep for note duration */
    usleep(duration_ms * 1000);

    /* Send note off - ignore errors for drum sounds that may already have decayed */
    fluid_synth_noteoff(g_metronome.synth, config.channel, note);
}

static void* metronome_thread_func(void *arg)
{
    (void)arg;  /* Unused */
    int beat_count = 0;
    long last_beat_time = get_time_ms();
    metronome_config_t config;

    printf("Metronome thread started\n");

    while (1) {
        pthread_mutex_lock(&g_metronome.mutex);
        if (!g_metronome.is_running) {
            pthread_mutex_unlock(&g_metronome.mutex);
            break;
        }
        memcpy(&config, &g_metronome.config, sizeof(metronome_config_t));
        pthread_mutex_unlock(&g_metronome.mutex);

        /* Calculate beat duration in milliseconds */
        long beat_duration_ms = (60000 / config.bpm);
        long current_time = get_time_ms();
        long elapsed = current_time - last_beat_time;

        if (elapsed >= beat_duration_ms) {
            /* Calculate which beat in the measure (0-based) */
            int beat_in_measure = beat_count % config.beats_per_measure;
            int is_accent = (beat_in_measure == 0);  /* First beat is accented */

            int note = is_accent ? config.accent_note : config.normal_note;
            int velocity = is_accent ? 100 : 80;

            play_note(note, velocity, config.duration_ms);

            printf("Metronome beat %d/%d (%s)\n", beat_in_measure + 1, config.beats_per_measure,
                   is_accent ? "ACCENT" : "normal");

            beat_count++;
            last_beat_time = current_time;
        }

        /* Sleep for a small amount to avoid busy waiting */
        usleep(10000);  /* 10ms */
    }

    printf("Metronome thread exiting\n");
    return NULL;
}
