#include "mp3_player.h"

#include <stdio.h>
#include <string.h>

#if defined(_WIN32)
#include <windows.h>
#include <process.h>
#else
#include <unistd.h>
#include <signal.h>
#include <sys/wait.h>
#endif

/* Track one PID per slot (0-7) for simultaneous playback */
static pid_t g_mp3_pids[8] = {-1, -1, -1, -1, -1, -1, -1, -1};
static char g_mp3_slot_paths[8][1024] = {{0}};

int stop_mp3_playback(int slot)
{
    /* slot = -1 means stop all; otherwise stop only the specified slot (0-7) */
    if(slot == -1)
    {
        /* Stop all slots */
        for(int i = 0; i < 8; i++)
        {
            if(g_mp3_pids[i] > 0)
            {
                kill(g_mp3_pids[i], SIGTERM);
                waitpid(g_mp3_pids[i], NULL, 0);
                g_mp3_pids[i] = -1;
            }
        }
    }
    else if(slot >= 0 && slot < 8)
    {
        /* Stop only this slot */
        if(g_mp3_pids[slot] > 0)
        {
            kill(g_mp3_pids[slot], SIGTERM);
            waitpid(g_mp3_pids[slot], NULL, 0);
            g_mp3_pids[slot] = -1;
        }
    }
    else
    {
        return -1;
    }

    return 0;
}

int play_mp3_file(const char *file_path, int slot)
{
    if(file_path == NULL || file_path[0] == '\0')
    {
        puts("Invalid MP3 path");
        return -1;
    }

    if(slot < 0 || slot >= 8)
    {
        printf("Invalid slot: %d (must be 0-7)\n", slot);
        return -1;
    }

    /* Only stop the MP3 for this specific slot, allowing others to continue */
    stop_mp3_playback(slot);

    pid_t pid = fork();
    if(pid < 0)
    {
        perror("fork failed");
        return -1;
    }

    if(pid == 0)
    {
#if defined(__APPLE__)
        execlp("afplay", "afplay", file_path, (char *)NULL);
#else
        execlp("mpg123", "mpg123", "-q", file_path, (char *)NULL);
#endif
        _exit(127);
    }

    g_mp3_pids[slot] = pid;
    printf("Started MP3 playback: %s (pid=%d, slot=%d)\n", file_path, (int)pid, slot + 1);
    return 0;
}

int set_mp3_slot_path(int slot, const char *file_path)
{
    if(slot < 1 || slot > 8)
    {
        return -1;
    }

    int idx = slot - 1;
    if(file_path == NULL || file_path[0] == '\0')
    {
        g_mp3_slot_paths[idx][0] = '\0';
        printf("[MP3-SLOT] slot=%d cleared\n", slot);
        fflush(stdout);
        return 0;
    }

    strncpy(g_mp3_slot_paths[idx], file_path, sizeof(g_mp3_slot_paths[idx]) - 1);
    g_mp3_slot_paths[idx][sizeof(g_mp3_slot_paths[idx]) - 1] = '\0';
    printf("[MP3-SLOT] slot=%d path=%s\n", slot, g_mp3_slot_paths[idx]);
    fflush(stdout);
    return 0;
}

int mp3_handle_cc_event(int cc, int value)
{
    if(cc < 16 || cc > 23 || value != 1)
    {
        return 0;
    }

    int slot = cc - 16;  /* 0-7 */
    if(g_mp3_slot_paths[slot][0] != '\0')
    {
        printf("[MP3-TRIGGER] slot=%d path=%s\n", slot + 1, g_mp3_slot_paths[slot]);
        fflush(stdout);
        return play_mp3_file(g_mp3_slot_paths[slot], slot);
    }

    printf("[MP3-TRIGGER] slot=%d has no mapped path\n", slot + 1);
    fflush(stdout);
    return 0;
}
