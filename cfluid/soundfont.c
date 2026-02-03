#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <dirent.h>
#include <fluidsynth.h>
#include "cfluid.h"

soundfont_t* load_soundfonts(fluid_synth_t *synth, int *count)
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
    
    *count = 0;
    
    /* Allocate initial array */
    fonts = (soundfont_t *)malloc(capacity * sizeof(soundfont_t));
    if(fonts == NULL)
    {
        return NULL;
    }
    
    /* Open the sf directory */
    dir = opendir("../sf");
    if(dir == NULL)
    {
        perror("Failed to open ../sf directory");
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
        
        /* Build full path */
        snprintf(fonts[index].path, sizeof(fonts[index].path), "../sf/%s", entry->d_name);
        
        /* Load the soundfont and store the ID */
        int id = fluid_synth_sfload(synth, fonts[index].path, 0);
        fonts[index].soundfont_id = id;
        
        if(id != FLUID_FAILED)
        {
            printf("Loaded: %s (ID: %d)\n", fonts[index].name, id);
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
        free(fonts);
    }
}
