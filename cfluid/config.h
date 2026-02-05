#ifndef CFLUID_CONFIG_H
#define CFLUID_CONFIG_H

#include <stddef.h>

#define MAX_CONFIG_LINES 64
#define MAX_CONFIG_KEY 256
#define MAX_CONFIG_VALUE 512

/* Helper struct to parse config file */
typedef struct {
    char keys[MAX_CONFIG_LINES][MAX_CONFIG_KEY];
    char values[MAX_CONFIG_LINES][MAX_CONFIG_VALUE];
    int count;
} config_t;

int parse_config_file(const char *config_path, config_t *config, char *soundfont_path);

#endif
