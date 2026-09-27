import __main__
import subprocess as sub
import time

def file_open_hidg0():
    
    # Open the file /dev/hidg0 for reading and writing.
    try:
        # Open the file in read/write mode
        file = open('/dev/hidg0', 'r+b')
        return file
    except FileNotFoundError:
        print("Error: /dev/hidg0 not found. Make sure the HID gadget is set up correctly.")
        return None

def send_keystroke(cmd, delay):

    file = file_open_hidg0()
    if file is None:
        return
    else:
        sub.run(cmd, shell=True)
        time.sleep(delay) 


send_keystroke("sudo hidtype Hello", 1)