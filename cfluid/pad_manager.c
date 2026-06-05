#include <fluidsynth.h>
#include "pad_manager.h"
#include "config.h"

#if defined(_WIN32)
#include <windows.h>
#define sleep(_t) Sleep(_t * 1000)
#include <process.h>
#define getpid _getpid
#else
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <pthread.h>
#endif

/* Global pointers for pad FluidSynth instance */
static fluid_settings_t *g_pad_settings = NULL;
static fluid_synth_t *g_pad_synth = NULL;
static fluid_audio_driver_t *g_pad_adriver = NULL;
static int g_pad_sfont_id = -1;
static int g_pad_is_playing = 0;
static pad_config_t g_pad_current_config = {0};
static pthread_t g_pad_fade_thread = 0;
static int g_pad_fade_active = 0;

int pad_manager_init(const char *config_path, const char *soundfont_path)
{
    char sf_dir[512] = {0};
    char sf_dir_temp[512] = {0};
    char fallback_path[512];
    char config_dir[512];
    config_t config = {0};
    
    /* Parse config file */
    if(config_path == NULL || config_path[0] == '\0')
    {
        printf("Error: config_path cannot be empty\n");
        return -1;
    }
    
    if(!parse_config_file(config_path, &config, sf_dir_temp))
    {
        printf("Error: Failed to parse config file\n");
        return -1;
    }
    
    /* Get the directory containing the config file */
    strncpy(config_dir, config_path, sizeof(config_dir) - 1);
    config_dir[sizeof(config_dir) - 1] = '\0';
    char *last_slash = strrchr(config_dir, '/');
    if(last_slash != NULL)
    {
        *last_slash = '\0';
    }
    else
    {
        config_dir[0] = '.';
        config_dir[1] = '\0';
    }
    
    printf("[PAD] Config directory: %s\n", config_dir);
    
    /* Determine soundfont path */
    if(soundfont_path != NULL && soundfont_path[0] != '\0')
    {
        strncpy(sf_dir, soundfont_path, sizeof(sf_dir) - 1);
        sf_dir[sizeof(sf_dir) - 1] = '\0';
    }
    else if(sf_dir_temp[0] == '\0')
    {
        snprintf(sf_dir, sizeof(sf_dir), "%s/sf", config_dir);
    }
    else if(sf_dir_temp[0] == '/')
    {
        strncpy(sf_dir, sf_dir_temp, sizeof(sf_dir) - 1);
        sf_dir[sizeof(sf_dir) - 1] = '\0';
    }
    else
    {
        snprintf(sf_dir, sizeof(sf_dir), "%s/%s", config_dir, sf_dir_temp);
    }
    
    printf("[PAD] Soundfont directory: %s\n", sf_dir);
    snprintf(fallback_path, sizeof(fallback_path), "%s/defaultGM.sf2", sf_dir);
    
    /* Create settings */
    g_pad_settings = new_fluid_settings();
    if(g_pad_settings == NULL)
    {
        printf("[PAD] Failed to create settings\n");
        return -1;
    }
    
    /* Apply config settings */
    for(int i = 0; i < config.count; i++)
    {
        const char *key = config.keys[i];
        const char *value = config.values[i];
        
        char *endptr;
        int int_value = strtol(value, &endptr, 10);
        
        if(*endptr == '\0' && endptr != value)
        {
            fluid_settings_setint(g_pad_settings, key, int_value);
            continue;
        }
        
        double double_value = strtod(value, &endptr);
        if(*endptr == '\0' && endptr != value)
        {
            fluid_settings_setnum(g_pad_settings, key, double_value);
            continue;
        }
        
        fluid_settings_setstr(g_pad_settings, key, value);
    }
    
    /* Create synth */
    g_pad_synth = new_fluid_synth(g_pad_settings);
    if(g_pad_synth == NULL)
    {
        printf("[PAD] Failed to create synth\n");
        delete_fluid_settings(g_pad_settings);
        return -1;
    }
    
    /* Create audio driver */
    printf("[PAD] Attempting to create audio driver...\n");
    fflush(stdout);
    g_pad_adriver = new_fluid_audio_driver(g_pad_settings, g_pad_synth);
    if(g_pad_adriver == NULL)
    {
        printf("[PAD] Failed to create audio driver with configured settings\n");
        printf("[PAD] Trying coreaudio as fallback...\n");
        fflush(stdout);
        
        /* Try coreaudio fallback */
        fluid_settings_setstr(g_pad_settings, "audio.driver", "coreaudio");
        g_pad_adriver = new_fluid_audio_driver(g_pad_settings, g_pad_synth);
        
        if(g_pad_adriver == NULL)
        {
            printf("[PAD] Failed to create audio driver with coreaudio fallback\n");
            fflush(stdout);
            delete_fluid_synth(g_pad_synth);
            delete_fluid_settings(g_pad_settings);
            return -1;
        }
        printf("[PAD] Successfully created fallback audio driver (coreaudio)\n");
        fflush(stdout);
    }
    else
    {
        printf("[PAD] Audio driver created successfully\n");
        fflush(stdout);
    }
    
    /* Load soundfont */
    g_pad_sfont_id = fluid_synth_sfload(g_pad_synth, fallback_path, 1);
    if(g_pad_sfont_id == -1)
    {
        printf("[PAD] Failed to load soundfont: %s\n", fallback_path);
        delete_fluid_audio_driver(g_pad_adriver);
        delete_fluid_synth(g_pad_synth);
        delete_fluid_settings(g_pad_settings);
        return -1;
    }
    
    printf("[PAD] Soundfont loaded successfully (id=%d)\n", g_pad_sfont_id);
    g_pad_is_playing = 0;
    
    return 0;
}

/* Fade-in thread function using MIDI Expression (CC#11) */
static void* pad_fade_thread_func(void *arg)
{
    if(!g_pad_is_playing || g_pad_synth == NULL)
        return NULL;
    
    int fade_ms = g_pad_current_config.fade_in_ms;
    int channel = 0;
    
    if(fade_ms <= 0)
        return NULL;
    
    printf("[PAD] Fade-in thread started: ramping expression 0->127 over %d ms\n", fade_ms);
    
    int step_count = (fade_ms + 19) / 20;  /* Fade over ~20ms steps for smoothness */
    int step_ms = fade_ms / step_count;
    
    for(int step = 1; step <= step_count && g_pad_fade_active; step++)
    {
        usleep(step_ms * 1000);
        
        if(!g_pad_fade_active || !g_pad_is_playing)
            break;
        
        /* Calculate current expression (0-127), ramp from 0 to 127 */
        int current_expr = (127 * step) / step_count;
        if(current_expr > 127) current_expr = 127;
        
        /* Set expression controller (CC#11) for smooth volume fade */
        fluid_synth_cc(g_pad_synth, channel, 11, current_expr);
        
        printf("[PAD] Fade step %d/%d: expression = %d\n", step, step_count, current_expr);
    }
    
    printf("[PAD] Fade-in complete, expression at maximum\n");
    g_pad_fade_active = 0;
    return NULL;
}

int pad_manager_cleanup(void)
{
    if(g_pad_is_playing)
    {
        pad_stop();
    }
    
    if(g_pad_adriver != NULL)
    {
        delete_fluid_audio_driver(g_pad_adriver);
        g_pad_adriver = NULL;
    }
    
    if(g_pad_synth != NULL)
    {
        delete_fluid_synth(g_pad_synth);
        g_pad_synth = NULL;
    }
    
    if(g_pad_settings != NULL)
    {
        delete_fluid_settings(g_pad_settings);
        g_pad_settings = NULL;
    }
    
    g_pad_is_playing = 0;
    return 0;
}

int pad_start(pad_config_t *config, const char *soundfont_name, const char *preset)
{
    if(g_pad_synth == NULL)
    {
        printf("[PAD] Synth not initialized\n");
        return -1;
    }
    
    if(config == NULL || config->notes == NULL || config->note_count <= 0)
    {
        printf("[PAD] Invalid pad config\n");
        return -1;
    }
    
    /* Stop any currently playing pad */
    pad_stop();
    
    /* Parse preset string (bank:program) */
    int bank = 0, program = 0;
    if(preset != NULL)
    {
        sscanf(preset, "%d:%d", &bank, &program);
    }
    
    int channel = 0;  /* Hardcoded to channel 0 */
    
    /* Set the program on the channel */
    fluid_synth_bank_select(g_pad_synth, channel, bank);
    fluid_synth_program_change(g_pad_synth, channel, program);
    
    printf("[PAD] Set channel %d to bank %d, program %d\n", channel, bank, program);
    
    /* Set initial expression level based on fade_in */
    if(config->fade_in_ms > 0)
    {
        fluid_synth_cc(g_pad_synth, channel, 11, 0);  /* Start silent for fade-in */
        printf("[PAD] Expression set to 0 for fade-in\n");
    }
    else
    {
        fluid_synth_cc(g_pad_synth, channel, 11, 127);  /* Full volume for immediate play */
        printf("[PAD] Expression set to 127 for immediate play\n");
    }
    
    /* Play all notes in the chord at full velocity */
    int velocity = config->velocity;
    for(int i = 0; i < config->note_count; i++)
    {
        int note = config->notes[i];
        fluid_synth_noteon(g_pad_synth, channel, note, velocity);
        printf("[PAD] Note ON: ch=%d note=%d velocity=%d\n", channel, note, velocity);
    }
    
    /* Store config and mark as playing */
    memcpy(&g_pad_current_config, config, sizeof(pad_config_t));
    g_pad_is_playing = 1;
    
    printf("[PAD] Pad started (sustain mode)\n");
    
    /* Start fade-in thread if needed */
    if(config->fade_in_ms > 0)
    {
        g_pad_fade_active = 1;
        if(pthread_create(&g_pad_fade_thread, NULL, pad_fade_thread_func, NULL) != 0)
        {
            printf("[PAD] Warning: Failed to create fade-in thread\n");
            /* Reset expression to full if thread creation failed */
            fluid_synth_cc(g_pad_synth, channel, 11, 127);
        }
    }
    
    return 0;
}

int pad_stop(void)
{
    if(!g_pad_is_playing || g_pad_synth == NULL)
    {
        return 0;
    }
    
    /* Stop fade-in thread if running */
    g_pad_fade_active = 0;
    if(g_pad_fade_thread != 0)
    {
        pthread_join(g_pad_fade_thread, NULL);
        g_pad_fade_thread = 0;
    }
    
    /* Turn off all notes on channel 0 (hardcoded) */
    int channel = 0;
    for(int i = 0; i < g_pad_current_config.note_count; i++)
    {
        int note = g_pad_current_config.notes[i];
        fluid_synth_noteoff(g_pad_synth, channel, note);
        printf("[PAD] Note OFF: ch=%d note=%d\n", channel, note);
    }
    
    g_pad_is_playing = 0;
    printf("[PAD] Pad stopped\n");
    return 0;
}

int pad_is_playing(void)
{
    return g_pad_is_playing;
}
