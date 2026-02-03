#!/usr/bin/env python3
"""Start pyFluidSynth and monitor MIDI events arriving at the synth input port.

Does NOT auto-connect any keyboard; it only reports whether events reach
the synth by tailing `aseqdump -p <synth_client>:0`.

Run with the workspace venv Python so bindings match your environment.
"""
import os
import re
import time
import subprocess
import signal
import sys

import fluidsynth


def aconnect_list():
    try:
        return subprocess.check_output(['aconnect', '-l'], text=True)
    except Exception:
        return ''


def find_synth_client_pid(pid, aconnect_out):
    for line in aconnect_out.splitlines():
        m = re.match(r"client (\d+): '(.+)'", line)
        if m:
            cid, name = m.group(1), m.group(2)
            if 'FLUID Synth' in name and str(pid) in name:
                return cid
    return None


def main():
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    SF = os.path.join(BASE_DIR, 'sf', 'defaultGM.sf2')

    fs = fluidsynth.Synth()
    # mirror your working CLI options
    fs.setting('audio.driver', 'pulseaudio')
    fs.setting('midi.driver', 'alsa_seq')
    fs.setting('midi.autoconnect', 1)
    fs.setting('synth.gain', 1.0)
    fs.start()

    if not os.path.exists(SF):
        print('Warning: SoundFont not found at', SF)
    else:
        sfid = fs.sfload(SF)
        fs.program_select(0, sfid, 0, 1)
        fs.program_select(1, sfid, 0, 48)

    pid = os.getpid()
    print('Started Synth, pid=', pid)

    # wait for the aconnect client to appear
    synth_cid = None
    for _ in range(10):
        acon = aconnect_list()
        synth_cid = find_synth_client_pid(pid, acon)
        if synth_cid:
            break
        time.sleep(0.3)

    if not synth_cid:
        print('Could not find FLUID Synth client for pid in aconnect -l')
        print('Full aconnect -l output:\n')
        print(acon)
        print('\nContinuing without aseqdump monitor...')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            fs.delete()
            return

    synth_port = '0'
    # Find which source clients are connected to the synth ports (e.g. '24:0')
    acon = aconnect_list()
    srcs = []
    cur_client = None
    for line in acon.splitlines():
        m = re.match(r"client (\d+): '(.+)'", line)
        if m:
            cur_client = m.group(1)
            cur_name = m.group(2)
            continue
        cm = re.search(r"Connected From:\s*(.+)", line)
        if cm and cur_client and 'FLUID Synth' in acon:
            # attach to the last seen client block
            entries = [s.strip() for s in cm.group(1).split(',')]
            for e in entries:
                # e is like '24:0'
                # if this client is connected to our synth_cid, record it
                # we'll check ports later
                srcs.extend(entries)

    # Filter unique srcs
    srcs = list(dict.fromkeys(srcs))

    if srcs:
        # prefer keyboard-like clients (Digital Piano) if available
        kbd_src = None
        for s in srcs:
            # check client name for 'Digital Piano'
            m = re.match(r"(\d+):\d+", s)
            if not m:
                continue
            cid = m.group(1)
            # search aconnect output for this client id name
            pat = re.compile(rf"client {cid}: '(.+)'")
            for line in acon.splitlines():
                pm = pat.match(line)
                if pm and 'Digital Piano' in pm.group(1):
                    kbd_src = s
                    break
            if kbd_src:
                break
        monitor_src = kbd_src or srcs[0]
        print(f'Monitoring MIDI events from source: {monitor_src}')
        try:
            aseq = subprocess.Popen(['aseqdump', '-p', monitor_src], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        except FileNotFoundError:
            print('aseqdump not found on PATH; cannot monitor incoming events.')
            aseq = None
    else:
        print('No source clients found connected to synth; running global aseqdump')
        try:
            aseq = subprocess.Popen(['aseqdump'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        except FileNotFoundError:
            print('aseqdump not found on PATH; cannot monitor incoming events.')
            aseq = None

    def sigint_handler(sig, frame):
        if aseq and aseq.poll() is None:
            aseq.terminate()
        fs.delete()
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)

    if aseq:
        try:
            for line in aseq.stdout:
                print(line.rstrip())
        except KeyboardInterrupt:
            pass
        finally:
            if aseq.poll() is None:
                aseq.terminate()

    fs.delete()


if __name__ == '__main__':
    main()
