#include <stdio.h>
#include <string.h>

#include "config.h"

int parse_config_file(const char *config_path, config_t *config, char *soundfont_path)
{
    FILE *file = fopen(config_path, "r");
    if(file == NULL)
    {
        printf("Warning: Could not open config file at %s\n", config_path);
        return 0;
    }

    char line[1024];
    config->count = 0;

    while(fgets(line, sizeof(line), file) != NULL && config->count < MAX_CONFIG_LINES)
    {
        /* Remove trailing newline */
        size_t len = strlen(line);
        if(len > 0 && line[len-1] == '\n')
            line[len-1] = '\0';

        /* Skip empty lines and comments */
        if(line[0] == '\0' || line[0] == '#')
            continue;

        /* Find the '=' separator */
        char *equals = strchr(line, '=');
        if(equals == NULL)
            continue;

        /* Split into key and value */
        *equals = '\0';
        char *key = line;
        char *value = equals + 1;

        /* Trim whitespace from key and value */
        while(*key && *key == ' ') key++;
        while(*value && *value == ' ') value++;
        
        size_t key_len = strlen(key);
        size_t value_len = strlen(value);
        while(key_len > 0 && key[key_len-1] == ' ') key[--key_len] = '\0';
        while(value_len > 0 && value[value_len-1] == ' ') value[--value_len] = '\0';

        /* Check if this is the soundfont_path setting */
        if(strcmp(key, "soundfont_path") == 0)
        {
            strncpy(soundfont_path, value, 511);
            soundfont_path[511] = '\0';
        }
        else if(strcmp(key, "mp3_max_upload_mb") == 0)
        {
            /* Consumed by the Django MP3 library, not FluidSynth. */
            continue;
        }
        else
        {
            /* Store other settings */
            strncpy(config->keys[config->count], key, MAX_CONFIG_KEY - 1);
            strncpy(config->values[config->count], value, MAX_CONFIG_VALUE - 1);
            config->keys[config->count][MAX_CONFIG_KEY - 1] = '\0';
            config->values[config->count][MAX_CONFIG_VALUE - 1] = '\0';
            config->count++;
        }
    }

    fclose(file);
    printf("Loaded %d settings from config file\n", config->count);
    return 1;
}
