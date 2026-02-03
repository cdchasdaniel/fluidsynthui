import re


def pull_out_preset(voice):
    full_string = voice.preset  # Example: "Grand Piano 0:18"
    # Pattern: (.*?) captures the name, (\d+) captures bank, (\d+) captures preset
    match = re.search(r'^(.*?)\s*(\d+):(\d+)$', full_string)
    if match:
        print("regex success")
        name_part, bank_str, num_str = match.groups()

        # Store the human-readable name in the preset_name field
        voice.preset_name = name_part.strip()

        # Convert the preset field to your standard "000:000" format
        voice.preset = f"{int(bank_str):03d}:{int(num_str):03d}"
    else:
        # Fallback if parsing fails
        voice.preset_name = full_string  # Keep the whole string if unparseable
        voice.preset = "000:000"
