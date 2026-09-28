import time
import sys
import os


NULL_CHAR = chr(0)

# Basic USB HID scancode mapping
KEY_MAP = {
    "a": (0, 0x04), "b": (0, 0x05), "c": (0, 0x06), "d": (0, 0x07),
    "e": (0, 0x08), "f": (0, 0x09), "g": (0, 0x0a), "h": (0, 0x0b),
    "i": (0, 0x0c), "j": (0, 0x0d), "k": (0, 0x0e), "l": (0, 0x0f),
    "m": (0, 0x10), "n": (0, 0x11), "o": (0, 0x12), "p": (0, 0x13),
    "q": (0, 0x14), "r": (0, 0x15), "s": (0, 0x16), "t": (0, 0x17),
    "u": (0, 0x18), "v": (0, 0x19), "w": (0, 0x1a), "x": (0, 0x1b),
    "y": (0, 0x1c), "z": (0, 0x1d),
    "1": (0, 0x1e), "2": (0, 0x1f), "3": (0, 0x20), "4": (0, 0x21),
    "5": (0, 0x22), "6": (0, 0x23), "7": (0, 0x24), "8": (0, 0x25),
    "9": (0, 0x26), "0": (0, 0x27),
    " ": (0, 0x2c), "\n": (0, 0x28),
    "A": (32, 0x04), "B": (32, 0x05), "C": (32, 0x06), "D": (32, 0x07),
    "E": (32, 0x08), "F": (32, 0x09), "G": (32, 0x0a), "H": (32, 0x0b),
    "I": (32, 0x0c), "J": (32, 0x0d), "K": (32, 0x0e), "L": (32, 0x0f),
    "M": (32, 0x10), "N": (32, 0x11), "O": (32, 0x12), "P": (32, 0x13),
    "Q": (32, 0x14), "R": (32, 0x15), "S": (32, 0x16), "T": (32, 0x17),
    "U": (32, 0x18), "V": (32, 0x19), "W": (32, 0x1a), "X": (32, 0x1b),
    "Y": (32, 0x1c), "Z": (32, 0x1d),
}


SPECIAL_KEYS = {
    "ENTER": (0, 0x28),
    "ESCAPE": (0, 0x29),
    "BACKSPACE": (0, 0x2a),
    "TAB": (0, 0x2b),
    "SPACE": (0, 0x2c),
}

MODIFIERS = {
    "CTRL": 0x01,
    "CONTROL": 0x01,
    "SHIFT": 0x02,
    "ALT": 0x04,
    "GUI": 0x08,
    "WIN": 0x08,
    "CMD": 0x08,
}

def write_report(report):
    with open("/dev/hidg0", "rb+") as fd:
        fd.write(report.encode("latin1"))

def release_keys():
    write_report(NULL_CHAR * 8)

def press_key(modifier, scancode):
    report = chr(modifier) + NULL_CHAR + chr(scancode) + (NULL_CHAR * 5)
    write_report(report)
    release_keys()

def press_hotkey(keys):
    if len(keys) < 2:
        raise ValueError("HOTKEY requires at least one modifier and one key")

    modifier = 0
    for key in keys[:-1]:
        modifier_code = MODIFIERS.get(key.upper())

        if modifier_code is None:
            raise ValueError(f"Unsupported modifier: {key}")
        modifier |= modifier_code

    final_key = keys[-1]

    key_data = SPECIAL_KEYS.get(final_key.upper()) or KEY_MAP.get(final_key.lower())
    if key_data is None:
        raise ValueError(f"Unsupported hotkey key: {final_key}")

    key_modifier, scancode = key_data
    press_key(modifier | key_modifier, scancode)

def type_string(text, delay=0.05):
    for char in text:
        if char in KEY_MAP:
            modifier, code = KEY_MAP[char]
            report = chr(modifier) + NULL_CHAR + chr(code) + (NULL_CHAR * 5)
            write_report(report)
            release_keys()
            time.sleep(delay)

# ----------------Parser Engine-----------------
class HIDParser:
    def __init__(self):
        pass

    def parse_line(self, line: str):
        line = line.strip()

        # Ignore empty lines and comments
        if not line or line.startswith('#'):
            return 

        parts = line.split(" ", 1)
        command = parts[0].upper()
        argument = parts[1] if len(parts) > 1 else ""


        if command == "STRING" or command == "TYPE":
            type_string(argument)

        elif command == "DELAY" or command == "SLEEP":
                time.sleep(float(argument) / 1000.0) # Convert milliseconds to seconds

        elif command in SPECIAL_KEYS:
            modifier, scancode = SPECIAL_KEYS[command]
            press_key(modifier, scancode)

        elif command == "HOTKEY":
            press_hotkey(argument.split())
        else:
            type_string(line)

    def run_file(self, filepath: str):
        if not os.path.exists(filepath):
            print(f"[parser Error] File not found: {filepath}")
            return

        print(f"Executing script: {filepath}")
        with open(filepath, 'r') as file:
            for line_number, line in enumerate(file, 1):
                try:
                    self.parse_line(line)
                except Exception as e:
                    print(f"[Parser Error] Failed on line {line_number}: '{line.strip()}' -> {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        parser = HIDParser()

        # 8 spaces of indentation
        if os.path.isfile(target):
            # 12 spaces of indentation
            parser.run_file(target)
        else:
            # 12 spaces of indentation
            type_string(" ".join(sys.argv[1:]))
    else:
        # 8 spaces of indentation
        print("Usage: hidtype <'text to type' OR path_to_script.txt>")