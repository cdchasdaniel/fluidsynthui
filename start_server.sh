#!/bin/bash
# FluidSynthUI server startup script
# Activates the Python virtual environment and runs Django development server

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# Change to project directory
cd "$SCRIPT_DIR"

# Prepare log directory for both systemd-user and manual runs
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Run the Django development server without the autoreloader
# Disabling the autoreloader prevents FluidSynth from being initialized twice
# (the autoreloader starts a monitor and a worker process).
# Capture stdout/stderr to a log file so we can diagnose FluidSynth audio issues.
# Force line-buffered output so C stdout/stderr (FluidSynth) appears in the log.
LOG_FILE="$LOG_DIR/server-$(date +%Y%m%d-%H%M%S).log"
echo "Starting Django server; logs -> $LOG_FILE"
{
	echo "===== start_server.sh $(date) ====="
	echo "PWD=$PWD"
	echo "USER=$USER"
	echo "XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
	echo "PULSE_SERVER=$PULSE_SERVER"
	echo "PYTHONUNBUFFERED=1"
} >> "$LOG_FILE"
# Keep only the 10 most recent server logs
ls -1t "$LOG_DIR"/server-*.log 2>/dev/null | tail -n +11 | xargs -r rm --
RUN_MAIN=true PYTHONUNBUFFERED=1 stdbuf -oL -eL python manage.py runserver --noreload 0.0.0.0:8080 >> "$LOG_FILE" 2>&1
