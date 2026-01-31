import time

import fluidsynth

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
fs.router_chan(0,0,0,1)
fs.router_par2(0,127,.33,0)
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