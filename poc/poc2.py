import time
import fluidsynth
from rtmidi.midiutil import open_midiinput
from rtmidi.midiconstants import NOTE_ON, NOTE_OFF, CONTROL_CHANGE, PROGRAM_CHANGE

# --- FluidSynth Setup ---
sf_path = "../sf/defaultGM.sf2"
fs = fluidsynth.Synth()
fs.start(driver='coreaudio')
sfid = fs.sfload(sf_path)
fs.program_select(0, sfid, 0, 0) # Channel 0, bank 0, preset 0

# --- MIDI Callback Function ---
def midi_callback(midievent, data):
    message, timestamp = midievent
    if message[0] & 0xF0 == NOTE_ON:
        channel = message[0] & 0x0F
        note = message[1]
        velocity = message[2]
        if velocity > 0:
            fs.noteon(channel, note, velocity)
        else:
            fs.noteoff(channel, note)
    elif message[0] & 0xF0 == NOTE_OFF:
        channel = message[0] & 0x0F
        note = message[1]
        fs.noteoff(channel, note)
    elif message[0] & 0xF0 == CONTROL_CHANGE:
        channel = message[0] & 0x0F
        controller = message[1]
        value = message[2]
        fs.cc(channel, controller, value)
    elif message[0] & 0xF0 == PROGRAM_CHANGE:
        channel = message[0] & 0x0F
        program = message[1]
        # fluidsynth uses bank/program selection. This is a simple program change
        fs.program_select(channel, sfid, 0, program)

# --- MIDI Input Setup ---
try:
    # 'midibus' is the name of the port, use a proper name for your setup
    # The second argument to open_midi_input can be a port number or name
    midiin, port_name = open_midiinput(port="Oxygen Pro Mini USB MIDI")
    midiin.set_callback(midi_callback)
    print(f"Opened MIDI input: {port_name}. Listening for events...")

    # Keep the script running
    while True:
        time.sleep(1)

except (EOFError, KeyboardInterrupt):
    print("\nExiting...")
finally:
    # Cleanup
    if 'midiin' in locals() and midiin:
        midiin.close_port()
    fs.delete()
    print("FluidSynth and MIDI port closed.")

