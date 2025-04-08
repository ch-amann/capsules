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

"""Capsule operations"""

import os
from pathlib import Path
from typing import Optional, List

import traceback

from .base import BaseCommandRunner, CommandResult
from utils import (
    get_capsule_dir, get_capsule_shared_dir, check_capsule_exists,
    check_template_exists, get_xpra_socket_path,
    get_capsule_shared_dir, get_template_mount_directories
)
from window_log import WindowLog

class CapsuleOps(BaseCommandRunner):
    def create_capsule(self, capsule_name: str, template_name: str, network_enabled: bool, port_mappings: List[str]) -> CommandResult:
        """Create a new capsule from template"""
        if check_capsule_exists(capsule_name):
            return CommandResult(False, f"Capsule/Template '{capsule_name}' already exists")
        if not check_template_exists(template_name):
            return CommandResult(False, f"Template '{template_name}' does not exist")

        try:
            capsule_dir = self._setup_capsule_directory(capsule_name, template_name)
            if not capsule_dir:
                return CommandResult(False, "Failed to setup capsule directory")

            return self._create_capsule_container(capsule_name, template_name, network_enabled, port_mappings)
        except Exception as e:
            WindowLog.log_error(f"Capsule creation failed: {e}")
            return CommandResult(False, str(e))

    def delete_capsule(self, capsule_name: str) -> CommandResult:
        """Delete capsule and its resources"""
        if not check_capsule_exists(capsule_name):
            return CommandResult(False, f"Capsule '{capsule_name}' does not exist")

        try:
            if self.xpra_is_attached(capsule_name):
                self.xpra_detach(capsule_name)

            self._run_command(["podman", "rm", "-f", "-t", "0", capsule_name], check=True)
            self._run_command(["podman", "unshare", "rm", "-rf", get_capsule_dir(capsule_name)], check=True)
            
            return CommandResult(success=True)
        except Exception as e:
            return CommandResult(False, str(e))

    def get_capsule_template(self, capsule_name: str) -> str:
        """Get template name for a capsule"""
        try:
            template_file = get_capsule_dir(capsule_name) / "template"
            if template_file.exists():
                return template_file.read_text().strip()
            return "unknown"
        except Exception as e:
            WindowLog.log_error(f"Failed to get template for {capsule_name}: {e}")
            return "unknown"

    def _setup_capsule_directory(self, capsule_name: str, template_name: str) -> Optional[Path]:
        """Setup directory structure for new capsule"""
        try:
            # Create main capsule directory
            capsule_dir = get_capsule_dir(capsule_name)
            capsule_dir.mkdir(parents=True, exist_ok=True)
            
            # Create socket directory
            (capsule_dir / "socket").mkdir(exist_ok=True)
            
            # Store template name
            (capsule_dir / "template").write_text(template_name)
            
            # Create socket directory
            socket_path = get_xpra_socket_path(capsule_name)
            socket_path.parent.mkdir(parents=True, exist_ok=True)

            return capsule_dir
        except Exception as e:
            WindowLog.log_error(f"Failed to setup capsule directory: {e}")
            return None

    def _create_capsule_container(self, capsule_name: str, template_name: str, network_enabled: bool, port_mappings: List[str]) -> CommandResult:
        """Create and configure capsule container"""
        try:
            # Read base image from template
            base_image = self.get_template_base_image(template_name)
            if not base_image:
                return CommandResult(False, f"Could not determine base image for template {template_name}")

            if ":" in base_image:
                base_image  = base_image.split(":")[0]
            
            # Setup overlay filesystem mounts
            overlay_fs_dir = get_capsule_dir(capsule_name) / "overlay_fs"
            template_mount_dirs = get_template_mount_directories(template_name)

            port_mapping_arguments = ""
            if network_enabled:
                for port_mapping in port_mappings:
                    port_mapping_arguments += f"-p {port_mapping} "
            
            overlay_fs_mounts = ""
            for dir_path in template_mount_dirs:
                basename = dir_path.name
                upper_dir = overlay_fs_dir / basename / "upper"
                work_dir = overlay_fs_dir / basename / "work"
                
                upper_dir.mkdir(parents=True, exist_ok=True)
                work_dir.mkdir(parents=True, exist_ok=True)

                overlay_fs_mounts += f"-v {dir_path}:/{basename}:O,upperdir={upper_dir},workdir={work_dir} "

            # Create capsule shared directory
            capsule_shared_dir = get_capsule_shared_dir(capsule_name)
            capsule_shared_dir.mkdir(parents=True, exist_ok=True)

            # Create container
            command = [
                "podman", "create",
                "--name", capsule_name,
                "--user", f"{os.getuid()}:{os.getuid()}",
                "--userns=keep-id",
                *port_mapping_arguments.split(),
                "-e", "DISPLAY=:0",
                "-v", f"{capsule_shared_dir}:/capsule_data",
                *overlay_fs_mounts.split(),
                f"{base_image}-capsule-image",
                "xpra", "start", 
                f"--bind=/capsule_data/xpra/{capsule_name}_socket",
                "--daemon=no"
            ]

            return self._run_command(command, log_output=True)

        except Exception as e:
            WindowLog.log_error(f"Failed to create capsule container: {e}")
            print(traceback.format_exc())
            return CommandResult(False, str(e))