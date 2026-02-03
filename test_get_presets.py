#!/usr/bin/env python3
"""
Test script to verify get_presets_for_file works
"""
import os
from pathlib import Path

# Add the patches module to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

# Import after path is set
from patches.synth import init_midi_device, get_soundfont_by_name

sf_path = os.path.join(str(Path(__file__).parent), "sf").encode('utf-8')
print(f"Initializing MIDI device with soundfont path: {sf_path.decode('utf-8')}")

# Initialize the MIDI device
result = init_midi_device(sf_path)
if result != 0:
    print(f"Failed to initialize MIDI device (error code: {result})")
    exit(1)

print("MIDI device initialized successfully\n")

# Test getting presets for a specific soundfont
test_files = [
    "defaultGM.sf2",
    "FluidR3_GM.sf2",
    "ModSynth_R1.sf2"
]

for sf_name in test_files:
    print(f"\nQuerying presets for: {sf_name}")
    soundfont = get_soundfont_by_name(sf_name.encode('utf-8'))
    
    if soundfont:
        sf = soundfont.contents
        print(f"  Found soundfont: {sf.name.decode('utf-8')}")
        print(f"  Preset count: {sf.preset_count}")
        
        if sf.preset_count > 0:
            print(f"  First 5 presets:")
            for i in range(min(5, sf.preset_count)):
                preset = sf.presets[i]
                print(f"    Bank {preset.bank:3d} Prog {preset.num:3d}: {preset.name.decode('utf-8')}")
    else:
        print(f"  Soundfont not found")

print("\n✓ Test completed successfully")
