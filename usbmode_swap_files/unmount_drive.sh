#!/bin/bash
set -e

if mountpoint -q /mnt/usb_drive; then
    umount /mnt/usb_drive
fi