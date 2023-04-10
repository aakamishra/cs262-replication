#!/bin/bash

# Set the target directory (use the current directory by default)
TARGET_DIR="${1:-.}"

# Find and delete files in the target directory starting with 'state_store'
find "$TARGET_DIR" -type f -name 'state_store*' -exec rm -f {} \;

echo "Deleted all files in '$TARGET_DIR' starting with 'state_store'"