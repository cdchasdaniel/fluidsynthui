CC ?= clang
CFLAGS ?= -O2 -fPIC -I.
LDFLAGS ?= $(shell pkg-config --libs fluidsynth)
CPPFLAGS ?= $(shell pkg-config --cflags fluidsynth)
METRONOME_LDFLAGS ?= $(LDFLAGS) -lpthread

LIB_NAME = libcfluid.so
METRONOME_LIB = libmetronome.so

.PHONY: all lib metronome clean

all: lib metronome

lib: $(LIB_NAME)

metronome: $(METRONOME_LIB)

$(LIB_NAME): cfluid.o soundfont.o config.o mp3_player.o
	$(CC) -shared -o $@ $^ $(LDFLAGS)

$(METRONOME_LIB): metronome.o config.o
	$(CC) -shared -o $@ $^ $(METRONOME_LDFLAGS)

cfluid.o: cfluid.c cfluid.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ cfluid.c

soundfont.o: soundfont.c cfluid.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ soundfont.c

config.o: config.c config.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ config.c

metronome.o: metronome.c metronome.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ metronome.c

mp3_player.o: mp3_player.c mp3_player.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ mp3_player.c

clean:
	rm -f *.o $(LIB_NAME) $(METRONOME_LIB)
