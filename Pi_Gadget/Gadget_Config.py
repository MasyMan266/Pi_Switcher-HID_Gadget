from pathlib import Path
import os
import subprocess as sup

from Pi_Gadget import Pi_def as pgdef
current_gadget_mode = pgdef.current_gadget_mode


def pi_config(cmdline=None, modules=None):
    config_dir = Path(__file__).resolve().parent / "config_swap_files"

    if cmdline is not None:
        old_cmdline_path = Path("/boot/firmware/cmdline.txt")
        new_cmdline_path = config_dir / cmdline

        if not new_cmdline_path.exists():
            raise FileNotFoundError(f"Missing cmdline swap file: {new_cmdline_path}")

        if not old_cmdline_path.exists():
            # Not running on real Pi hardware (e.g. tlocal dev/debugging); nothing to swap.
            print(f"Skipping cmdline swap, not found: {old_cmdline_path}")
        else:
            temp = old_cmdline_path.read_text()
            old_cmdline_path.write_text(new_cmdline_path.read_text())
            new_cmdline_path.write_text(temp)

    if modules is not None:
        old_modules_path = Path("/etc/modules")
        new_modules_path = config_dir / modules

        if not new_modules_path.exists():
            raise FileNotFoundError(f"Missing modules swap file: {new_modules_path}")

        if not old_modules_path.exists():
            print(f"Skipping modules swap, not found: {old_modules_path}")
        else:
            temp = old_modules_path.read_text()
            old_modules_path.write_text(new_modules_path.read_text())
            new_modules_path.write_text(temp)




def apply_default_gadget_mode():
    if current_gadget_mode == "libcomposite":
        pi_config("cmdline_Drive.txt", "modules_libcomposite.txt")
    elif current_gadget_mode == "drive":
        pi_config("cmdline_Drive.txt", "modules_Drive.txt")
    elif current_gadget_mode == "serial":
        pi_config("cmdline_USBSerial.txt", "modules_USBSerial.txt")

def start_serial():
    try:
        sup.run("sudo /home/masyman266/RaspberryPiCode/usbmode_swap_files/start_serial.sh", shell=True, check=False)
    except Exception as exc:
        print(f"Failed to start serial gadget: {exc}")

def stop_current_gadget():
    try:
        sup.run("sudo /home/masyman266/RaspberryPiCode/usbmode_swap_files/stop_gadget.sh", shell=True, check=False)
    except Exception as exc:
        print(f"Failed to stop current gadget: {exc}")


def unmount_drive():
    try:
        sup.run("sudo /home/masyman266/RaspberryPiCode/usbmode_swap_files/unmount_drive.sh", shell=True, check=False)
    except Exception as exc:
        print(f"Failed to unmount drive: {exc}")

def mount_drive(path, folder):
    try:
        sup.run(f"sudo /home/masyman266/RaspberryPiCode/usbmode_swap_files/mount_drive.sh {path} {folder}", shell=True, check=False)
        
    except Exception as exc:
        print(f"Failed to mount drive: {exc}")

def start_mass_storage(path):
    try:
        sup.run(f"sudo /home/masyman266/RaspberryPiCode/usbmode_swap_files/start_mass_storage.sh {path}", shell=True, check=False)
    except Exception as exc:
        print(f"Failed to start mass storage: {exc}")

def switch_to_drive_mode():
    try:
        stop_current_gadget()
        pi_config("cmdline_Drive.txt", "modules_Drive.txt")
        mount_drive("/piusb.bin", "/mnt/usbdrive")
        start_mass_storage("/piusb.bin")

    except Exception as exc:
        print(f"Failed to switch to drive mode: {exc}")


def restore_default_gadget_mode():
    try:
        stop_current_gadget()
        unmount_drive()
        apply_default_gadget_mode()
    except Exception as exc:
        print(f"Failed to restore default gadget mode: {exc}")

def switch_to_serial_mode():
    try:
        stop_current_gadget()
        pi_config("cmdline_USBSerial.txt", "modules_USBSerial.txt")
        if os.path.ismount("/mnt/usbdrive"):
            unmount_drive()
        start_serial()
    except Exception as exc:
        print(f"Failed to switch to serial mode: {exc}")
