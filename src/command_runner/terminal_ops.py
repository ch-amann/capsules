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

"""Terminal operations"""

import shutil
import subprocess
from typing import Optional

from .base import BaseCommandRunner, CommandResult
from misc import Entity
from utils import get_capsule_shared_dir, get_template_shared_dir
from window_log import WindowLog
from settings import Settings

class TerminalOps(BaseCommandRunner):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.potential_terminals = [
            "gnome-terminal", "konsole", "xfce4-terminal",
            "lxterminal", "mate-terminal", "terminator",
            "alacritty", "kitty", "st"
        ]

    def _get_terminal_command(self, terminal: str, container_name: str) -> list[str]:
        """Get the correct command format for different terminals"""
        podman_cmd = ["podman", "exec", "-it", container_name, "/bin/bash"]
        
        # Terminal-specific command formats
        if terminal in ["gnome-terminal", "mate-terminal"]:
            return [terminal, "--", *podman_cmd]
        elif terminal == "konsole":
            return [terminal, "-e", *podman_cmd]
        elif terminal == "xfce4-terminal":
            return [terminal, "--command", " ".join(podman_cmd)]
        elif terminal in ["kitty", "alacritty"]:
            return [terminal, *podman_cmd]
        else:
            # Default format for other terminals
            return [terminal, "-e", *podman_cmd]

    def open_terminal(self, container_name: str) -> CommandResult:
        """Open a terminal in the specified container"""
        WindowLog.log_info(f"Opening terminal in: {container_name}")

        terminal = self._find_terminal()
        if not terminal:
            return CommandResult(False, "No suitable terminal found")

        try:
            cmd = self._get_terminal_command(terminal, container_name)
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return CommandResult(success=True)
        except Exception as e:
            return CommandResult(False, f"Failed to open terminal: {e}")

    def open_shared_directory(self, entity_type: Entity, name: str) -> CommandResult:
        """Open shared directory for template or capsule"""
        path = get_capsule_shared_dir(name) if entity_type == Entity.CAPSULE else get_template_shared_dir(name)
        
        try:
            subprocess.run(["xdg-open", path], check=False)
            return CommandResult(success=True)
        except Exception as e:
            return CommandResult(False, f"Failed to open directory: {e}")

    def _find_terminal(self) -> Optional[str]:
        """Find available terminal emulator"""
        global_config = self.settings.get_global_config()
        terminal = global_config["DEFAULT"].get("terminal")
        if terminal and shutil.which(terminal):
            return terminal

        for terminal in self.potential_terminals:
            if shutil.which(terminal):
                return terminal

        WindowLog.log_error(f"No terminal found. Please install one of: {', '.join(self.potential_terminals)}")
        return None