#ifndef MP3_PLAYER_H
#define MP3_PLAYER_H

#ifdef __cplusplus
extern "C" {
#endif

int play_mp3_file(const char *file_path, int slot);
int stop_mp3_playback(int slot);

#ifdef __cplusplus
}
#endif

#endif
