#!/usr/bin/env bash
set -euo pipefail

# Resolve soundfont path relative to this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SF="$SCRIPT_DIR/../sf/defaultGM.sf2"

OUTFILE="/tmp/acon_cli.txt"

fluidsynth -a pulseaudio -m alsa_seq -o midi.autoconnect=1 -g 1.0 "$SF" &
FS_PID=$!
# give it a moment to start and register with ALSA
sleep 1
aconnect -l > "$OUTFILE" || true
# stop fluidsynth
kill $FS_PID || true
sleep 0.2
wait $FS_PID 2>/dev/null || true
echo "$OUTFILE"
