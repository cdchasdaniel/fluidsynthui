#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <dirent.h>
#include <fluidsynth.h>
#include "cfluid.h"

/* Forward declaration */
static void load_presets(fluid_synth_t *synth, int soundfont_id, soundfont_t *font);

/*
 * Load all presets from a soundfont by iterating through actual presets
 */
static void load_presets(fluid_synth_t *synth, int soundfont_id, soundfont_t *font)
{
    fluid_sfont_t *sfont;
    fluid_preset_t *preset;
    preset_t *temp_presets = NULL;
    int preset_idx = 0;
    int capacity = 128;  /* Start with reasonable capacity */
    
    if(font == NULL || synth == NULL)
        return;
    
    /* Get the soundfont object */
    sfont = fluid_synth_get_sfont_by_id(synth, soundfont_id);
    if(sfont == NULL)
    {
        printf("  Failed to get soundfont object\n");
        return;
    }
    
    /* Allocate initial preset array */
    temp_presets = (preset_t *)malloc(capacity * sizeof(preset_t));
    if(temp_presets == NULL)
    {
        fprintf(stderr, "Failed to allocate preset array\n");
        return;
    }
    
    /* Iterate through all presets in the soundfont */
    /* FluidSynth 2.5.2 uses iteration_start and iteration_next */
    fluid_sfont_iteration_start(sfont);
    while((preset = fluid_sfont_iteration_next(sfont)) != NULL)
    {
        /* Resize if needed */
        if(preset_idx >= capacity)
        {
            capacity *= 2;
            preset_t *temp = (preset_t *)realloc(temp_presets, capacity * sizeof(preset_t));
            if(temp == NULL)
            {
                fprintf(stderr, "Failed to reallocate preset array\n");
                free(temp_presets);
                return;
            }
            temp_presets = temp;
        }
        
        /* Store preset info */
        temp_presets[preset_idx].bank = fluid_preset_get_banknum(preset);
        temp_presets[preset_idx].num = fluid_preset_get_num(preset);
        strncpy(temp_presets[preset_idx].name, fluid_preset_get_name(preset), 
                sizeof(temp_presets[preset_idx].name) - 1);
        temp_presets[preset_idx].name[sizeof(temp_presets[preset_idx].name) - 1] = '\0';
        preset_idx++;
    }
    
    /* Allocate and copy only the found presets */
    if(preset_idx > 0)
    {
        font->presets = (preset_t *)malloc(preset_idx * sizeof(preset_t));
        if(font->presets != NULL)
        {
            memcpy(font->presets, temp_presets, preset_idx * sizeof(preset_t));
            font->preset_count = preset_idx;
            printf("  Found %d presets\n", preset_idx);
        }
    }
    
    free(temp_presets);
}

soundfont_t* load_soundfonts(fluid_synth_t *synth, const char *sf_path, int *count)
{
    DIR *dir;
    struct dirent *entry;
    soundfont_t *fonts = NULL;
    int capacity = 10;
    int index = 0;
    
    if(count == NULL || synth == NULL)
    {
        if(count != NULL)
            *count = 0;
        return NULL;
    }
    
    if(sf_path == NULL || sf_path[0] == '\0')
    {
        fprintf(stderr, "Soundfont path not provided\n");
        *count = 0;
        return NULL;
    }
    
    /* Allocate initial array */
    fonts = (soundfont_t *)malloc(capacity * sizeof(soundfont_t));
    if(fonts == NULL)
    {
        return NULL;
    }
    
    /* Initialize all soundfont structs */
    for(int i = 0; i < capacity; i++)
    {
        fonts[i].presets = NULL;
        fonts[i].preset_count = 0;
    }
    
    /* Open the sf directory */
    dir = opendir(sf_path);
    if(dir == NULL)
    {
        perror("Failed to open soundfont directory");
        free(fonts);
        return NULL;
    }
    
    /* Read directory entries */
    while((entry = readdir(dir)) != NULL)
    {
        /* Skip . and .. */
        if(strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0)
        {
            continue;
        }
        
        /* Check if file has .sf2 extension */
        const char *ext = strrchr(entry->d_name, '.');
        if(ext == NULL || strcmp(ext, ".sf2") != 0)
        {
            continue;
        }
        
        /* Resize array if needed */
        if(index >= capacity)
        {
            capacity *= 2;
            soundfont_t *temp = (soundfont_t *)realloc(fonts, capacity * sizeof(soundfont_t));
            if(temp == NULL)
            {
                fprintf(stderr, "Failed to allocate memory for soundfonts\n");
                closedir(dir);
                free(fonts);
                *count = 0;
                return NULL;
            }
            fonts = temp;
        }
        
        /* Copy filename to name */
        strncpy(fonts[index].name, entry->d_name, sizeof(fonts[index].name) - 1);
        fonts[index].name[sizeof(fonts[index].name) - 1] = '\0';
        
        /* Build full path using provided sf_path */
        snprintf(fonts[index].path, sizeof(fonts[index].path), "%s/%s", sf_path, entry->d_name);
        
        /* Load the soundfont and store the ID */
        int id = fluid_synth_sfload(synth, fonts[index].path, 0);
        fonts[index].soundfont_id = id;
        
        if(id != FLUID_FAILED)
        {
            printf("Loaded: %s (ID: %d)\n", fonts[index].name, id);
            load_presets(synth, id, &fonts[index]);
        }
        else
        {
            printf("Failed to load: %s\n", fonts[index].name);
        }
        
        index++;
    }
    
    closedir(dir);
    *count = index;
    
    if(index == 0)
    {
        free(fonts);
        return NULL;
    }
    
    return fonts;
}

void free_soundfonts(soundfont_t *fonts, int count)
{
    if(fonts != NULL)
    {
        for(int i = 0; i < count; i++)
        {
            if(fonts[i].presets != NULL)
            {
                free(fonts[i].presets);
            }
        }
        free(fonts);
    }
}
