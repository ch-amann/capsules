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
# This script copies directories to the mountpoint /template_volume/
# These directories can be mounted as overlay fs in non-template containers

set -e

DIRECTORIES=(/bin /sbin /lib /lib64 /etc /usr /home)

for dir in "${DIRECTORIES[@]}"; do
    # Check if the directory exists and is not a symlink
    if [[ -d "$dir" && ! -L "$dir" ]]; then
        echo $dir
        sudo cp -rp "$dir" "/template_volume/"
    fi
done


echo "Successfully copied template directories"
