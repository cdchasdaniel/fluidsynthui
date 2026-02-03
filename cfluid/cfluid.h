#ifndef CFLUID_H
#define CFLUID_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    char name[256];
    char path[512];
    int soundfont_id;
} soundfont_t;

int init_midi_device(const char *soundfont_path);
int cleanup_midi_device(void);
int set_channel_preset(int channel_num, const char *soundfont_name, const char *preset_name);
int route_notes_to_channel(int channel, int min_note, int max_note, int volume, int transpose);
int route_sustain_to_channel(int channel);
soundfont_t* load_soundfonts(fluid_synth_t *synth, int *count);
void free_soundfonts(soundfont_t *fonts, int count);

#ifdef __cplusplus
}
#endif

#endif
