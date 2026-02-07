#ifndef CFLUID_H
#define CFLUID_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int bank;
    int num;
    char name[256];
} preset_t;

typedef struct {
    char name[256];
    char path[512];
    int soundfont_id;
    preset_t *presets;
    int preset_count;
} soundfont_t;

int init_midi_device(const char *config_path);
int cleanup_midi_device(void);
int set_channel_preset(int channel_num, const char *soundfont_name, const char *preset_name);
int route_notes_to_channel(int channel, int min_note, int max_note, int volume, int transpose);
int route_cc_to_channel(int channel, int cc_num);
int route_sustain_to_channel(int channel);
int route_volume_to_channel(int channel);
int clear_router(void);
int set_reverb(double room_size, double damping, double width, double level);
soundfont_t* load_soundfonts(fluid_synth_t *synth, const char *sf_path, int *count);
void free_soundfonts(soundfont_t *fonts, int count);
soundfont_t* get_soundfont_by_name(const char *filename);
int get_soundfont_count(void);
void* get_synth(void);
void noteon(int channel, int note, int velocity);
void noteoff(int channel, int note);
void program_change(int channel, int program);

#ifdef __cplusplus
}
#endif

#endif
