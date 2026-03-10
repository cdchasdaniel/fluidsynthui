#ifndef MP3_PLAYER_H
#define MP3_PLAYER_H

#ifdef __cplusplus
extern "C" {
#endif

int play_mp3_file(const char *file_path);
int stop_mp3_playback(void);
int set_mp3_slot_path(int slot, const char *file_path);
int mp3_handle_cc_event(int cc, int value);

#ifdef __cplusplus
}
#endif

#endif
