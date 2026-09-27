#!/bin/bash
set -e

sudo modprobe -r g_mass_storage || true
sudo modprobe g_mass_storage file=/piusb.bin removable=1 stall=0 ro=1
