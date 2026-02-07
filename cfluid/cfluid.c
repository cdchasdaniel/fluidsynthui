#include <fluidsynth.h>
#include "cfluid.h"
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
#endif


/* Global pointers to keep track of FluidSynth resources */
static fluid_settings_t *g_settings = NULL;
static fluid_synth_t *g_synth = NULL;
static fluid_audio_driver_t *g_adriver = NULL;
static fluid_midi_driver_t *g_mdriver = NULL;
static fluid_midi_router_t *g_router = NULL;
static int g_sfont_id = -1;
static soundfont_t *g_soundfonts = NULL;
static int g_sfont_count = 0;

int init_midi_device(const char *config_path)
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
    
    printf("Config file: %s\n", config_path);
    printf("Config directory: %s\n", config_dir);
    printf("Soundfont path from config: %s\n", sf_dir_temp[0] ? sf_dir_temp : "(empty)");
    
    /* If soundfont_path wasn't in config, use default */
    if(sf_dir_temp[0] == '\0')
    {
        snprintf(sf_dir, sizeof(sf_dir), "%s/sf", config_dir);
    }
    else if(sf_dir_temp[0] == '/')
    {
        /* Absolute path - use as is */
        strncpy(sf_dir, sf_dir_temp, sizeof(sf_dir) - 1);
        sf_dir[sizeof(sf_dir) - 1] = '\0';
    }
    else
    {
        /* Relative path - make it relative to config directory */
        snprintf(sf_dir, sizeof(sf_dir), "%s/%s", config_dir, sf_dir_temp);
    }
    
    printf("Final soundfont directory: %s\n", sf_dir);
    snprintf(fallback_path, sizeof(fallback_path), "%s/defaultGM.sf2", sf_dir);
    
    /* Create the settings. */
    g_settings = new_fluid_settings();
    if(g_settings == NULL)
    {
        puts("Failed to create the settings!");
        return -1;
    }
 
    /* Apply settings from config file */
    for(int i = 0; i < config.count; i++)
    {
        const char *key = config.keys[i];
        const char *value = config.values[i];
        
        /* Check if value looks like a number (try int/float first) */
        char *endptr;
        int int_value = strtol(value, &endptr, 10);
        
        /* If the entire string was consumed, it's an integer */
        if(*endptr == '\0' && endptr != value)
        {
            if(fluid_settings_setint(g_settings, key, int_value) == FLUID_OK)
            {
                printf("Setting %s = %d\n", key, int_value);
                continue;
            }
        }
        
        /* Try as double/float */
        double double_value = strtod(value, &endptr);
        if(*endptr == '\0' && endptr != value)
        {
            if(fluid_settings_setnum(g_settings, key, double_value) == FLUID_OK)
            {
                printf("Setting %s = %f\n", key, double_value);
                continue;
            }
        }
        
        /* Fall back to string */
        if(fluid_settings_setstr(g_settings, key, value) == FLUID_OK)
        {
            printf("Setting %s = %s\n", key, value);
        }
        else
        {
            printf("Warning: Could not set %s = %s\n", key, value);
        }
    }
 
    /* Create the synthesizer. */
    g_synth = new_fluid_synth(g_settings);
    if(g_synth == NULL)
    {
        puts("Failed to create the synth!");
        goto err;
    }
 
    /* Load all available soundfonts from the specified directory */
    g_soundfonts = load_soundfonts(g_synth, sf_dir, &g_sfont_count);
    if(g_soundfonts == NULL || g_sfont_count == 0)
    {
        printf("No soundfonts found in %s. Trying default fallback...\n", sf_dir);
        g_sfont_id = fluid_synth_sfload(g_synth, fallback_path, 1);
    }
    else
    {
        /* Use the first soundfont as default */
        g_sfont_id = g_soundfonts[0].soundfont_id;
        printf("Using soundfont %s as default.\n", g_soundfonts[0].name);
    }
    
    if(g_sfont_id == FLUID_FAILED)
    {
        puts("Loading soundfonts failed!");
        goto err;
    }
 
    /* Create the audio driver. The synthesizer starts playing as soon
       as the driver is created. If the configured audio driver fails
       (device busy or not available), try a small set of fallback
       drivers before giving up and running headless. This helps when
       users switch between PulseAudio/ALSA or run from CLI vs GUI. */
    g_adriver = new_fluid_audio_driver(g_settings, g_synth);
    if(g_adriver == NULL)
    {
        #ifdef __APPLE__
        const char *fallbacks[] = {"coreaudio", "portaudio", "dummy"};
        #else
        const char *fallbacks[] = {"pulseaudio", "alsa", "jack", "portaudio", "dummy"};
        #endif

        printf("Warning: Failed to create the audio driver; trying fallbacks.\n");

        for(size_t i = 0; i < sizeof(fallbacks)/sizeof(fallbacks[0]); ++i)
        {
            if(fluid_settings_setstr(g_settings, "audio.driver", fallbacks[i]) != FLUID_OK)
                continue;

            g_adriver = new_fluid_audio_driver(g_settings, g_synth);
            if(g_adriver != NULL)
            {
                printf("Audio driver '%s' created successfully as fallback.\n", fallbacks[i]);
                break;
            }

            printf("Fallback driver '%s' failed.\n", fallbacks[i]);
        }

        if(g_adriver == NULL)
        {
            printf("Warning: All audio driver attempts failed; continuing without audio.\n");
        }
    }
    else
    {
        printf("Audio driver created successfully.\n");
    }
 
    /* Create the MIDI router for note routing */
    g_router = new_fluid_midi_router(g_settings, fluid_synth_handle_midi_event, g_synth);
    if(g_router == NULL)
    {
        puts("Failed to create the MIDI router!");
        goto err;
    }
    
    /* Create the MIDI driver that uses the router */
    g_mdriver = new_fluid_midi_driver(g_settings, fluid_midi_router_handle_midi_event, g_router);
    if(g_mdriver == NULL)
    {
        puts("Failed to create the MIDI driver!");
        goto err;
    }
    
    printf("MIDI device initialized. Waiting for MIDI input...\n");
    return 0;
    
err:
    /* Clean up on error */
    if(g_mdriver != NULL) delete_fluid_midi_driver(g_mdriver);
    if(g_router != NULL) delete_fluid_midi_router(g_router);
    if(g_adriver != NULL) delete_fluid_audio_driver(g_adriver);
    if(g_synth != NULL) delete_fluid_synth(g_synth);
    if(g_settings != NULL) delete_fluid_settings(g_settings);
    
    g_settings = NULL;
    g_synth = NULL;
    g_adriver = NULL;
    g_mdriver = NULL;
    g_router = NULL;
    
    return -1;
}

int cleanup_midi_device(void)
{
    /* Clean up */
    if(g_mdriver != NULL) delete_fluid_midi_driver(g_mdriver);
    if(g_router != NULL) delete_fluid_midi_router(g_router);
    if(g_adriver != NULL) delete_fluid_audio_driver(g_adriver);
    if(g_synth != NULL) delete_fluid_synth(g_synth);
    if(g_settings != NULL) delete_fluid_settings(g_settings);
    if(g_soundfonts != NULL) free_soundfonts(g_soundfonts, g_sfont_count);
    
    g_settings = NULL;
    g_synth = NULL;
    g_adriver = NULL;
    g_mdriver = NULL;
    g_router = NULL;
    g_soundfonts = NULL;
    g_sfont_count = 0;
    
    return 0;
}

int set_channel_preset(int channel_num, const char *soundfont_name, const char *preset_name)
{
    int bank, prog;
    int sfont_id = g_sfont_id;
    
    if(g_synth == NULL)
    {
        puts("Synth not initialized!");
        return -1;
    }
    
    /* If soundfont name provided, find it in the global array */
    if(soundfont_name != NULL && soundfont_name[0] != '\0')
    {
        int found = 0;
        for(int i = 0; i < g_sfont_count; i++)
        {
            if(strcmp(g_soundfonts[i].name, soundfont_name) == 0)
            {
                sfont_id = g_soundfonts[i].soundfont_id;
                found = 1;
                break;
            }
        }
        
        if(!found)
        {
            printf("Soundfont not found: %s\n", soundfont_name);
            return -1;
        }
        
        if(sfont_id == FLUID_FAILED)
        {
            printf("Soundfont failed to load: %s\n", soundfont_name);
            return -1;
        }
    }
    
    /* Parse the preset name to get bank and program numbers
     * Expected format: "bank:program" or "program" (bank defaults to 0)
     * Examples: "0:0" for piano, "0:24" for guitar, etc.
     */
    if(sscanf(preset_name, "%d:%d", &bank, &prog) == 2)
    {
        /* Both bank and program specified */
    }
    else if(sscanf(preset_name, "%d", &prog) == 1)
    {
        /* Only program specified, use bank 0 */
        bank = 0;
    }
    else
    {
        printf("Invalid preset format: %s (use 'bank:program' or 'program')\n", preset_name);
        return -1;
    }
    
    /* Select the preset for the specified MIDI channel */
    fluid_synth_program_select(g_synth, channel_num, sfont_id, bank, prog);
    printf("Channel %d: Preset set to bank %d, program %d (soundfont ID: %d)\n", channel_num, bank, prog, sfont_id);
    
    return 0;
}

int route_notes_to_channel(int channel, int min_note, int max_note, int volume, int transpose)
{
    fluid_midi_router_rule_t *rule;
    
    if(g_synth == NULL || g_router == NULL)
    {
        puts("Synth or router not initialized!");
        return -1;
    }
    
    /* Create a new router rule for note events */
    rule = new_fluid_midi_router_rule();
    if(rule == NULL)
    {
        puts("Failed to create router rule!");
        return -1;
    }
    
    /* Route from channel 0 to the specified channel */
    fluid_midi_router_rule_set_chan(rule, 0, 0, 0.0, channel);
    
    /* Set note range with transpose */
    fluid_midi_router_rule_set_param1(rule, min_note, max_note, 1.0, transpose);
    
    /* Set velocity range with volume offset */
    fluid_midi_router_rule_set_param2(rule, 0, 127, 0.0, volume);
    
    /* Add the rule to the router */
    if(fluid_midi_router_add_rule(g_router, rule, FLUID_MIDI_ROUTER_RULE_NOTE) != FLUID_OK)
    {
        delete_fluid_midi_router_rule(rule);
        puts("Failed to add router rule!");
        return -1;
    }
    
    printf("Routed notes [%d-%d] to channel %d (transpose: %d, volume: %d)\n",
           min_note, max_note, channel, transpose, volume);
    
    /* Also route volume control for this channel */
    route_volume_to_channel(channel);
    
    return 0;
}

int clear_router(void)
{
    if(g_router == NULL)
    {
        puts("Router not initialized!");
        return -1;
    }

    fluid_midi_router_clear_rules(g_router);
    return 0;
}

int route_cc_to_channel(int channel, int cc_num)
{
    fluid_midi_router_rule_t *rule;
    
    if(g_synth == NULL || g_router == NULL)
    {
        puts("Synth or router not initialized!");
        return -1;
    }
    
    /* Create a new router rule for CC events */
    rule = new_fluid_midi_router_rule();
    if(rule == NULL)
    {
        puts("Failed to create router rule!");
        return -1;
    }
    
    /* Route CC from channel 0 to the specified channel */
    fluid_midi_router_rule_set_chan(rule, 0, 0, 0.0, channel);
    
    /* Set to only match the specified CC number */
    fluid_midi_router_rule_set_param1(rule, cc_num, cc_num, 1.0, 0);
    
    /* Add the rule to the router for CC events */
    if(fluid_midi_router_add_rule(g_router, rule, FLUID_MIDI_ROUTER_RULE_CC) != FLUID_OK)
    {
        delete_fluid_midi_router_rule(rule);
        puts("Failed to add CC router rule!");
        return -1;
    }
    
    printf("Routed CC %d to channel %d\n", cc_num, channel);
    
    return 0;
}

int route_sustain_to_channel(int channel)
{
    /* Route sustain pedal (CC 64) to the specified channel */
    return route_cc_to_channel(channel, 64);
}

int route_volume_to_channel(int channel)
{
    /* Route volume control (CC 7) to the specified channel */
    return route_cc_to_channel(channel, 7);
}

int set_reverb(double room_size, double damping, double width, double level)
{
    if(g_synth == NULL)
    {
        puts("Synth not initialized!");
        return -1;
    }
    
    /* Set reverb parameters on the synthesizer using individual setters */
    /* Note: These setters are deprecated in FluidSynth 2.5.2 but are the only available API */
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
    fluid_synth_set_reverb_roomsize(g_synth, room_size);
    fluid_synth_set_reverb_damp(g_synth, damping);
    fluid_synth_set_reverb_width(g_synth, width);
    fluid_synth_set_reverb_level(g_synth, level);
#pragma GCC diagnostic pop
    
    printf("Reverb set: room_size=%.2f, damping=%.2f, width=%.2f, level=%.2f\n",
           room_size, damping, width, level);
    
    return 0;
}

#ifdef CFLUID_STANDALONE
int main(int argc, char **argv)
{
    const char *soundfont_path = NULL;
    if(argc > 1)
    {
        soundfont_path = argv[1];
    }

    int result = init_midi_device(soundfont_path);
    if(result == 0)
    {
        printf("Play notes on your MIDI device (press Ctrl+C to stop)\n");

        /* Keep the program running */
        while(1)
        {
            sleep(1);
        }
    }

    cleanup_midi_device();
    return result;
}
#endif

/*
 * Get a soundfont by filename
 */
soundfont_t* get_soundfont_by_name(const char *filename)
{
    if(filename == NULL || g_soundfonts == NULL || g_sfont_count == 0)
        return NULL;
    
    for(int i = 0; i < g_sfont_count; i++)
    {
        if(strcmp(g_soundfonts[i].name, filename) == 0)
        {
            return &g_soundfonts[i];
        }
    }
    
    return NULL;
}

/*
 * Get total number of loaded soundfonts
 */
int get_soundfont_count(void)
{
    return g_sfont_count;
}

/*
 * Get the synth handle for direct access
 */
void* get_synth(void)
{
    return (void*)g_synth;
}

/*
 * Play a note on a channel
 */
void noteon(int channel, int note, int velocity)
{
    if(g_synth != NULL)
    {
        fluid_synth_noteon(g_synth, channel, note, velocity);
    }
}

/*
 * Stop a note on a channel
 */
void noteoff(int channel, int note)
{
    if(g_synth != NULL)
    {
        fluid_synth_noteoff(g_synth, channel, note);
    }
}

/*
 * Change program (instrument) on a channel
 */
void program_change(int channel, int program)
{
    if(g_synth != NULL)
    {
        fluid_synth_program_change(g_synth, channel, program);
    }
}