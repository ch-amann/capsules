#!/bin/bash
#
# This file is part of Capsules.
#
# Capsules is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Capsules is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Capsules. If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2025 Christian Amann
#
#
# This script copies directories in '/' to '/mnt/root_dirs'.
# This script is used when setting up a template. The copied directories will be mounted into the template container
# Each capsule will also mount these directories, but as overlay fs instead.


DEST_DIR="/mnt/root_dirs"
if [ ! -d "$DEST_DIR" ]; then
    echo "Error: $DEST_DIR does not exist. Exiting."
    exit 1
fi
EXCLUDE_DIRS=("/tmp" "/proc" "/dev" "/mnt" "/sys" "/boot")

exclude_dir() {
    for excl in "${EXCLUDE_DIRS[@]}"; do
        if [ "$1" == "$excl" ]; then
            return 0  # Exclude the directory
        fi
    done
    return 1  # Not in the exclude list
}

find / -maxdepth 1 -type d ! -name ".*" ! -path "/" ! -type l | while read dir; do
    if exclude_dir "$dir"; then
        continue
    fi
    dir_name=$(basename "$dir")
    echo "Copying $dir to $DEST_DIR/$dir_name"
    cp -rp "$dir" "$DEST_DIR/$dir_name"
done
echo "Directory copy completed."
