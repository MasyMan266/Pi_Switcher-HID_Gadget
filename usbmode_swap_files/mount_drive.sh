#!/bin/bash
set -e

if ! mountpoint -q "$2"; then
    sudo mount "$1" "$2"
fi