import os
import ctypes
import fluidsynth
from fluidsynth import _fl

# --- 1. Define the missing C-Signatures ---
# These prototypes allow Python to talk to the hidden iteration logic in the C library.
_fl.fluid_synth_get_sfont_by_id.argtypes = [ctypes.c_void_p, ctypes.c_uint]
_fl.fluid_synth_get_sfont_by_id.restype = ctypes.c_void_p

_fl.fluid_sfont_iteration_start.argtypes = [ctypes.c_void_p]
_fl.fluid_sfont_iteration_next.argtypes = [ctypes.c_void_p]
_fl.fluid_sfont_iteration_next.restype = ctypes.c_void_p

_fl.fluid_preset_get_name.argtypes = [ctypes.c_void_p]
_fl.fluid_preset_get_name.restype = ctypes.c_char_p
_fl.fluid_preset_get_banknum.argtypes = [ctypes.c_void_p]
_fl.fluid_preset_get_banknum.restype = ctypes.c_int
_fl.fluid_preset_get_num.argtypes = [ctypes.c_void_p]
_fl.fluid_preset_get_num.restype = ctypes.c_int


def print_presets(sf_path):
    if not os.path.exists(sf_path):
        print(f"Error: File not found at {sf_path}")
        return

    # Initialize Synth (No audio driver needed just for scanning)
    fs = fluidsynth.Synth()

    # Load SoundFont
    sfid = fs.sfload(sf_path)
    if sfid == -1:
        print("Error: Failed to load SoundFont.")
        return

    # Get the SoundFont pointer from the synth
    sfont = _fl.fluid_synth_get_sfont_by_id(fs.synth, sfid)

    if sfont:
        print(f"\nScanning: {os.path.basename(sf_path)}")
        print(f"{'Bank':<6} | {'Num':<4} | {'Instrument Name'}")
        print("-" * 40)

        # Start iteration
        _fl.fluid_sfont_iteration_start(sfont)

        while True:
            # Get next preset pointer
            preset_ptr = _fl.fluid_sfont_iteration_next(sfont)
            if not preset_ptr:
                break

            # Extract data from the C pointer
            bank = _fl.fluid_preset_get_banknum(preset_ptr)
            num = _fl.fluid_preset_get_num(preset_ptr)
            name = _fl.fluid_preset_get_name(preset_ptr).decode('utf-8')

            print(f"{bank:<6} | {num:<4} | {name}")

    # Clean up
    fs.sfunload(sfid)
    fs.delete()


if __name__ == "__main__":
    # Replace with the actual path to your defaultGM.sf2
    PATH_TO_SF2 = "../sf/defaultGM.sf2"
    print_presets(PATH_TO_SF2)
