#!/usr/bin/env python3
"""Quick MP3 playback test through the cfluid C bridge.

Usage:
  python poc/test_mp3_playback.py
  python poc/test_mp3_playback.py --file wind.mp3 --stop-after 5
"""

import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from patches.synth import play_mp3_file, stop_mp3_playback


def main() -> int:
    parser = argparse.ArgumentParser(description="Play an MP3 file via cfluid C bridge")
    parser.add_argument("--file", default="wind.mp3", help="MP3 filename inside static/mp3")
    parser.add_argument(
        "--stop-after",
        type=float,
        default=0.0,
        help="Seconds to wait before calling stop_mp3_playback (0 = don't auto-stop)",
    )
    args = parser.parse_args()

    mp3_path = PROJECT_ROOT / "static" / "mp3" / args.file

    if not mp3_path.exists():
        print(f"ERROR: File not found: {mp3_path}")
        return 1

    print(f"Playing: {mp3_path}")
    result = play_mp3_file(str(mp3_path).encode("utf-8"))
    if result != 0:
        print("ERROR: play_mp3_file returned non-zero")
        return 2

    if args.stop_after > 0:
        time.sleep(args.stop_after)
        stop_mp3_playback()
        print("Stopped playback.")
        return 0

    print("Playback started. Press Ctrl+C to stop test.")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_mp3_playback()
        print("Stopped playback.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
