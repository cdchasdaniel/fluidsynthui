CC ?= clang
CFLAGS ?= -O2 -fPIC -I.
LDFLAGS ?= $(shell pkg-config --libs fluidsynth)
CPPFLAGS ?= $(shell pkg-config --cflags fluidsynth)

LIB_NAME = libcfluid.so

.PHONY: all lib clean

all: lib

lib: $(LIB_NAME)

$(LIB_NAME): cfluid.o soundfont.o config.o
	$(CC) -shared -o $@ $^ $(LDFLAGS)

cfluid.o: cfluid.c cfluid.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ cfluid.c

soundfont.o: soundfont.c cfluid.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ soundfont.c

config.o: config.c config.h
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ config.c

clean:
	rm -f *.o $(LIB_NAME)
