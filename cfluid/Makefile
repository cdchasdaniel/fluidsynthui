CC ?= clang
CFLAGS ?= -O2 -fPIC -I.
LDFLAGS ?= $(shell pkg-config --libs fluidsynth)
CPPFLAGS ?= $(shell pkg-config --cflags fluidsynth)
METRONOME_LDFLAGS ?= $(LDFLAGS) -lpthread
PAD_LDFLAGS ?= $(LDFLAGS) -lpthread

LIB_NAME = libcfluid.so
METRONOME_LIB = libmetronome.so
PAD_LIB = libpad.so

.PHONY: all lib metronome pad clean

all: lib metronome pad

lib: $(LIB_NAME)

metronome: $(METRONOME_LIB)

pad: $(PAD_LIB)

$(LIB_NAME): cfluid.o soundfont.o config.o mp3_player.o
	$(CC) -shared -o $@ $^ $(LDFLAGS)

$(METRONOME_LIB): metronome.o config.o
	$(CC) -shared -o $@ $^ $(METRONOME_LDFLAGS)

$(PAD_LIB): pad_manager.o config.o
	$(CC) -shared -o $@ $^ $(PAD_LDFLAGS)

cfluid.o: cfluid.c cfluid.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ cfluid.c

soundfont.o: soundfont.c cfluid.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ soundfont.c

config.o: config.c config.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ config.c

metronome.o: metronome.c metronome.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ metronome.c

pad_manager.o: pad_manager.c pad_manager.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ pad_manager.c

mp3_player.o: mp3_player.c mp3_player.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ mp3_player.c

clean:
	rm -f *.o $(LIB_NAME) $(METRONOME_LIB) $(PAD_LIB)
