import time

import fluidsynth

from patches.synth.pyfluidsynth_old import note_to_midi

fs = fluidsynth.Synth()
fs.setting('midi.autoconnect',1)
fs.start()

# 2. Load SoundFont (Replace with your actual path)
sf_path = "../sf/defaultGM.sf2"
sfid = fs.sfload(sf_path)
fs.program_select(0, sfid, 0, 1)
fs.program_select(1, sfid, 0, 48)

fs.router_begin("note")
# channel 1 note events get routed to channel 0
fs.router_chan(0,0,0,0)
# channel 1 note events only occur between A0 and C5
fs.router_par1(note_to_midi("C#5"),note_to_midi("A8"),1,0)
fs.router_end()

fs.router_begin("note")
# channel 1 note events get routed to channel 0
fs.router_chan(0,0,0,1)
# channel 1 note events only occur between A0 and C5
fs.router_par1(note_to_midi("A0"),note_to_midi("C5"),1,0)
fs.router_end()

try:
    while True:
        time.sleep(1)
except (EOFError, KeyboardInterrupt):
    print("\nExiting...")
finally:
    # Cleanup
    fs.delete()
    print("FluidSynth and MIDI port closed.")