#include <fluidsynth.h>
#include "cfluid.h"
 
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

int init_midi_device(const char *soundfont_path)
{
    
    /* Create the settings. */
    g_settings = new_fluid_settings();
    if(g_settings == NULL)
    {
        puts("Failed to create the settings!");
        return -1;
    }
 
    /* Change the settings if necessary*/
    fluid_settings_setint(g_settings, "midi.autoconnect", 1);
 
    /* Create the synthesizer. */
    g_synth = new_fluid_synth(g_settings);
    if(g_synth == NULL)
    {
        puts("Failed to create the synth!");
        goto err;
    }
 
    /* Load all available soundfonts from the sf directory */
    g_soundfonts = load_soundfonts(g_synth, &g_sfont_count);
    if(g_soundfonts == NULL || g_sfont_count == 0)
    {
        printf("No soundfonts found. Trying default fallback...\n");
        g_sfont_id = fluid_synth_sfload(g_synth, "../sf/defaultGM.sf2", 1);
    }
    else
    {
        /* Use the first soundfont as default */
        g_sfont_id = g_soundfonts[0].soundfont_id;
    }
    
    if(g_sfont_id == FLUID_FAILED)
    {
        puts("Loading soundfonts failed!");
        goto err;
    }
 
    /* Create the audio driver. The synthesizer starts playing as soon
       as the driver is created. */
    g_adriver = new_fluid_audio_driver(g_settings, g_synth);
    if(g_adriver == NULL)
    {
        puts("Failed to create the audio driver!");
        goto err;
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
    fluid_midi_router_rule_set_param2(rule, 0, 127, 1.0, volume);
    
    /* Add the rule to the router */
    if(fluid_midi_router_add_rule(g_router, rule, FLUID_MIDI_ROUTER_RULE_NOTE) != FLUID_OK)
    {
        delete_fluid_midi_router_rule(rule);
        puts("Failed to add router rule!");
        return -1;
    }
    
    printf("Routed notes [%d-%d] to channel %d (transpose: %d, volume: %d)\n",
           min_note, max_note, channel, transpose, volume);
    
    return 0;
}

int route_sustain_to_channel(int channel)
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
    
    /* Route sustain pedal (CC 64) from channel 0 to the specified channel */
    fluid_midi_router_rule_set_chan(rule, 0, 0, 0.0, channel);
    
    /* Set to only match CC 64 (sustain pedal) */
    fluid_midi_router_rule_set_param1(rule, 64, 64, 1.0, 0);
    
    /* Add the rule to the router for CC events */
    if(fluid_midi_router_add_rule(g_router, rule, FLUID_MIDI_ROUTER_RULE_CC) != FLUID_OK)
    {
        delete_fluid_midi_router_rule(rule);
        puts("Failed to add sustain router rule!");
        return -1;
    }
    
    printf("Routed sustain pedal to channel %d\n", channel);
    
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