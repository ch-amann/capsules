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
import getpass
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

# Capsule operations
def get_capsule_dir(capsule_name: str) -> Path:
    """Get capsule configuration directory"""
    return CapsulesDir / capsule_name

def get_capsule_shared_dir(capsule_name: str) -> Path:
    """Get shared capsule directory"""
    return get_capsule_dir(capsule_name) / "shared"

def check_capsule_exists(capsule_name: str) -> bool:
    """Check if a capsule exists (directory or container)"""
    return get_capsule_dir(capsule_name).exists() or check_podman_container_exists(capsule_name)

# Template operations
def get_template_dir(template_name: str) -> Path:
    """Get template configuration directory"""
    return TemplateDir / template_name

def get_template_shared_dir(template_name: str) -> Path:
    """Get shared template directory"""
    return get_template_dir(template_name) / "shared"

def get_template_rootfs_dir(template_name: str) -> Path:
    """Get shared template directory"""
    return get_template_dir(template_name) / "rootfs"

def get_template_rootfs_directories(template_name: str) -> List[Path]:
    """Get list of template mount directories"""
    rootfs_path = get_template_rootfs_dir(template_name)
    return [dir_path for dir_path in rootfs_path.glob("*/") if dir_path.is_dir()]

def get_template_mount_directories(template_name: str) -> List[Path]:
    """Get list of template mount directories"""
    rootfs_path = get_template_rootfs_dir(template_name)
    return [dir_path for dir_path in rootfs_path.glob("*/") if dir_path.is_dir()]

def check_template_exists(template_name: str) -> bool:
    """Check if a template exists (directory and container)"""
    return get_template_dir(template_name).exists() and check_podman_container_exists(template_name)

# Xpra socket operations
def get_xpra_socket_path(capsule_name: str) -> Path:
    """Get the actual Xpra socket path in the container volume"""
    capsule_shared_dir = get_capsule_shared_dir(capsule_name)
    return capsule_shared_dir / "xpra" / f"{capsule_name}_socket"

# Container existence checks
def check_podman_container_exists(container_name: str) -> bool:
    """Check if a podman container exists"""
    command = f"podman ps -a --format '{{{{.Names}}}}' | grep -w {container_name}"
    return os.system(command) == 0

