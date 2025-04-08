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

"""Template operations"""

import os
import shutil
from typing import List, Optional
from pathlib import Path

from .base import BaseCommandRunner, CommandResult
from misc import ProjectBaseDir, CapsulesDir
from utils import (
    get_template_dir, get_template_volume, check_template_exists
)
from window_log import WindowLog

class TemplateOps(BaseCommandRunner):
    def create_template(self, template_name: str, base_image: str, network_enabled: bool) -> CommandResult:
        """Create a new template container"""
        if check_template_exists(template_name):
            return CommandResult(False, f"Template/Capsule '{template_name}' already exists")

        try:
            if not self._ensure_base_image(base_image):
                return CommandResult(False, "Failed to prepare base image")

            template_dir = self._setup_template_directory(template_name, base_image)
            if not template_dir:
                return CommandResult(False, "Failed to setup template directory")

            return self._create_template_container(template_name, base_image, network_enabled)
        except Exception as e:
            WindowLog.log_error(f"Template creation failed: {e}")
            return CommandResult(False, str(e))

    def delete_template(self, template_name: str) -> CommandResult:
        """Delete template and its resources"""
        if not check_template_exists(template_name):
            return CommandResult(False, f"Template '{template_name}' does not exist")

        dependent_capsules = self._get_dependent_capsules(template_name)
        if dependent_capsules:
            return CommandResult(False, f"Template has dependent capsules: {', '.join(dependent_capsules)}")

        try:
            self._run_command(["podman", "rm", "-f", "-t", "0", template_name], check=True)
            self._run_command(["podman", "unshare", "rm", "-rf", get_template_dir(template_name)], check=True)
            self._run_command(["podman", "volume", "rm", get_template_volume(template_name)], check=True)
            return CommandResult(success=True)
        except Exception as e:
            return CommandResult(False, str(e))

    def get_available_base_images(self) -> List[str]:
        """Get list of available base images"""
        try:
            images_dir = ProjectBaseDir / "images"
            if not images_dir.exists():
                WindowLog.log_error(f"Images directory not found: {images_dir}")
                return []
                
            return [
                directory.name 
                for directory in images_dir.iterdir() 
                if directory.is_dir() and (directory / "Dockerfile").exists()
            ]
        except Exception as e:
            WindowLog.log_error(f"Failed to get available base images: {e}")
            return []

    def get_template_base_image(self, template_name: str) -> str:
        """Get base image name for a template"""
        try:
            base_image_file = get_template_dir(template_name) / "base_image"
            if base_image_file.exists():
                return base_image_file.read_text().strip()
            return "unknown"
        except Exception as e:
            WindowLog.log_error(f"Failed to get base image for {template_name}: {e}")
            return "unknown"

    def _ensure_base_image(self, base_image: str) -> bool:
        """Ensure base image exists and is up to date"""
        try:
            dockerfile = ProjectBaseDir / "images" / base_image / "Dockerfile"
            if not dockerfile.exists():
                return False

            image_name = f"{base_image}-capsule-image"
            self._run_command(
                ["podman", "build", "-t", image_name, 
                 "--build-arg", f"USER_ID={os.getuid()}", 
                 "--build-arg", f"GROUP_ID={os.getgid()}", 
                 dockerfile.parent],
                log_output=True
            )
            return True
        except Exception as e:
            WindowLog.log_error(f"Failed to ensure base image: {e}")
            return False

    def _get_dependent_capsules(self, template_name: str) -> List[str]:
        """Get list of capsules dependent on a template"""
        dependent = []
        for capsule_dir in CapsulesDir.glob("*"):
            template_file = capsule_dir / "template"
            if template_file.exists() and template_file.read_text().strip() == template_name:
                dependent.append(capsule_dir.name)
        return dependent

    def _setup_template_directory(self, template_name: str, base_image: str) -> Optional[Path]:
        """Setup directory structure for new template"""
        try:
            # Create main template directory
            template_dir = get_template_dir(template_name)
            template_dir.mkdir(parents=True, exist_ok=True)
            
            # Create and setup scripts directory
            template_script_dir = template_dir / "scripts"
            template_script_dir.mkdir(exist_ok=True)
            
            # Copy scripts from project base
            script_dir = ProjectBaseDir / "scripts"
            for script in script_dir.glob("*"):
                shutil.copy2(script, template_script_dir)
            
            # Store base image info
            (template_dir / "base_image").write_text(base_image)
            
            return template_dir
            
        except Exception as e:
            WindowLog.log_error(f"Failed to setup template directory: {e}")
            return None

    def _create_template_container(self, template_name: str, base_image: str, network_enabled: bool) -> CommandResult:
        """Create and configure template container"""
        try:
            template_volume = get_template_volume(template_name)
            
            # Create template volume
            result = self._run_command(["podman", "volume", "create", template_volume])
            if not result.success:
                WindowLog.log_error(f"Failed to create volume: {result.error_message}")
                return result

            # Setup template volume with initial content
            template_script_dir = get_template_dir(template_name) / "scripts"
            result = self._run_command([
                "podman", "run", "--rm",
                "--name", f"{template_name}_SETUP",
                "--network=none",
                "--userns=keep-id",
                "-v", f"{template_script_dir}:/scripts",
                "-v", f"{template_volume}:/template_volume",
                f"{base_image}-capsule-image",
                "sudo", "/scripts/copy_template_dirs.sh"
            ], log_output=True)
            
            if not result.success:
                return result

            # Get mount directories for overlayfs
            volume_path = Path.home() / ".local/share/containers/storage/volumes" / template_volume / "_data"
            mounts = [f"-v {d}:/{d.name}" for d in volume_path.glob("*/")]
            
            # Create template container
            network_name = "pasta" if network_enabled else "none"
            
            command = [
                "podman", "create",
                "--name", template_name,
                "--userns=keep-id",
                f"--network={network_name}",
                *" ".join(mounts).split(),
                f"{base_image}-capsule-image",
                "sleep", "infinity"
            ]
            
            return self._run_command(command, log_output=True)
            
        except Exception as e:
            WindowLog.log_error(f"Failed to create template container: {e}")
            return CommandResult(False, str(e))