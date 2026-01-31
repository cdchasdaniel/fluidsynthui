import time
import fluidsynth
import rtmidi

fs = fluidsynth.Synth()
fs.setting('midi.autoconnect',1)
fs.start()

# 2. Load SoundFont (Replace with your actual path)
sf_path = "../sf/defaultGM.sf2"
sfid = fs.sfload(sf_path)
fs.program_select(0, sfid, 0, 0)  # Select first instrument

# 3. Setup MIDI Input from Oxygen Pro Mini
midi_in = rtmidi.MidiIn()
ports = midi_in.get_ports()


def set_port():
    # Search for the M-Audio Oxygen Pro Mini port
    target_port = None
    for i, port_name in enumerate(ports):
        print(port_name)
        if "Oxygen Pro Mini" in port_name:
            target_port = i
            break
    if target_port is not None:
        midi_in.open_port(target_port)
        print(f"Connected to: {ports[target_port]}")
    else:
        print("Oxygen Pro Mini not found. Please check your connection.")
        fs.delete()
        exit()


#set_port()

# 4. Main Event Loop
print("Synthesizer Ready! Press Ctrl+C to exit.")
try:
    while True:
        # Check for new MIDI messages
        msg_and_time = midi_in.get_message()
        if msg_and_time:
            msg, timestamp = msg_and_time
            status = msg[0] & 0xF0  # Message type
            channel = msg[0] & 0x0F
            note = msg[1]
            velocity = msg[2]

            # Handle Note On (144) and Note Off (128)
            if status == 0x90:  # Note On
                if velocity > 0:
                    fs.noteon(channel, note, velocity)
                else:  # Some controllers use velocity 0 for Note Off
                    fs.noteoff(channel, note)
            elif status == 0x80:  # Note Off
                fs.noteoff(channel, note)

        time.sleep(0.001)  # Short sleep to prevent high CPU usage
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    midi_in.close_port()
    fs.delete()
