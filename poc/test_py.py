#!/usr/bin/env python3
import os
import time
import subprocess
import fluidsynth

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SF = os.path.join(BASE_DIR, 'sf', 'defaultGM.sf2')

fs = fluidsynth.Synth()
fs.setting('audio.driver', 'pulseaudio')
fs.setting('midi.driver', 'alsa_seq')
fs.setting('midi.autoconnect', 1)
fs.setting('synth.gain', 1.0)
fs.start()
sfid = fs.sfload(SF)

time.sleep(1)
try:
    out = subprocess.check_output(['aconnect', '-l'], text=True)
except Exception:
    out = ''
open('/tmp/acon_py.txt', 'w').write(out)
fs.delete()
print('/tmp/acon_py.txt')
