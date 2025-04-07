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
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Copyright (C) 2025 Christian Amann

"""
Utility functions for Capsules application.
Provides path handling, container operations, and system configuration.
"""

import os
from pathlib import Path
from typing import Tuple, List
from dataclasses import dataclass

from misc import CapsulesDir, TemplateDir

@dataclass
class ContainerPaths:
    """Container-specific path definitions"""
    PODMAN_VOLUMES: Path = Path.home() / ".local/share/containers/storage/volumes"
    SUBUID_FILE: Path = Path("/etc/subuid")
    SUBGID_FILE: Path = Path("/etc/subgid")

# Path operations
def get_project_base_dir() -> Path:
    """Get the project's base directory"""
    return Path(__file__).parent.parent.resolve()

def get_capsule_dir(capsule_name: str) -> Path:
    """Get capsule configuration directory"""
    return CapsulesDir / capsule_name

def get_template_dir(template_name: str) -> Path:
    """Get template configuration directory"""
    return TemplateDir / template_name

def get_capsule_volume(capsule_name: str) -> str:
    """Get capsule volume name"""
    return f"{capsule_name}_capsule_volume"

def get_template_volume(template_name: str) -> str:
    """Get template volume name"""
    return f"{template_name}_template_volume"

# Xpra socket operations
def get_xpra_socket_path(capsule_name: str) -> Path:
    """Get the actual Xpra socket path in the container volume"""
    capsule_volume = get_capsule_volume(capsule_name)
    return ContainerPaths.PODMAN_VOLUMES / capsule_volume / "_data/xpra" / f"{capsule_name}_socket"

def get_xpra_socket_symlink_path(capsule_name: str) -> Path:
    """Get the Xpra socket symlink path"""
    return get_capsule_dir(capsule_name) / "socket" / "socket"

# System configuration
def get_user_id_mappings() -> Tuple[str, str]:
    """Get UID/GID mappings for rootless containers"""
    try:
        user_id = os.getuid()
        group_id = os.getgid()
        next_user_id = user_id + 1
        next_group_id = group_id + 1
        
        # Get max subuid/subgid values
        def read_max_id(filepath: Path, username: str) -> int:
            with open(filepath) as f:
                for line in f:
                    if line.startswith(username):
                        return int(line.split(':')[2])
            raise ValueError(f"No entry found for user {username}")
        
        username = os.getlogin()
        max_users = read_max_id(ContainerPaths.SUBUID_FILE, username)
        max_groups = read_max_id(ContainerPaths.SUBGID_FILE, username)
        
        uid_mappings = (
            f"--uidmap 0:1:{user_id} "
            f"--uidmap {user_id}:0:1 "
            f"--uidmap {next_user_id}:{next_user_id}:{max_users - user_id}"
        )
        gid_mappings = (
            f"--gidmap 0:1:{group_id} "
            f"--gidmap {group_id}:0:1 "
            f"--gidmap {next_group_id}:{next_group_id}:{max_groups - group_id}"
        )
        
        return uid_mappings, gid_mappings
    except Exception as e:
        raise RuntimeError(f"Failed to get user ID mappings: {e}")

# Container existence checks
def check_podman_container_exists(container_name: str) -> bool:
    """Check if a podman container exists"""
    command = f"podman ps -a --format '{{{{.Names}}}}' | grep -w {container_name}"
    return os.system(command) == 0

def check_capsule_exists(capsule_name: str) -> bool:
    """Check if a capsule exists (directory or container)"""
    return get_capsule_dir(capsule_name).exists() or check_podman_container_exists(capsule_name)

def check_template_exists(template_name: str) -> bool:
    """Check if a template exists (directory and container)"""
    return get_template_dir(template_name).exists() and check_podman_container_exists(template_name)

# Mount point operations
def get_capsule_mount_point(capsule_name: str) -> Path:
    """Get capsule volume mount point"""
    return ContainerPaths.PODMAN_VOLUMES / get_capsule_volume(capsule_name) / "_data"

def get_template_mount_point(template_name: str) -> Path:
    """Get template volume mount point"""
    return ContainerPaths.PODMAN_VOLUMES / get_template_volume(template_name) / "_data"

def get_template_mount_directories(template_name: str) -> List[Path]:
    """Get list of template mount directories"""
    volume_path = get_template_mount_point(template_name)
    return [dir_path for dir_path in volume_path.glob("*/") if dir_path.is_dir()]
