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

"""Podman-specific operations"""

import subprocess
from typing import Optional

from .base import BaseCommandRunner, CommandResult
from window_log import WindowLog

class PodmanOps(BaseCommandRunner):
    def podman_command(
        self, 
        command: str, 
        container_name: str, 
        extra: Optional[str] = None, 
        wait_for_finish: bool = True
    ) -> CommandResult:
        """Execute a podman command"""
        cmd = ["podman"] + command.split() + [container_name]
        # Add any extra arguments
        if extra:
            cmd.extend(extra.split())
        
        if wait_for_finish:
            return self._run_command(cmd)
        else:
            try:
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                return CommandResult(success=True)
            except Exception as e:
                WindowLog.log_error(f"podman_command error: {e}")
                return CommandResult(success=False, error_message=str(e))

    def podman_allows_rootless(self) -> bool:
        result = subprocess.run(
            ["podman", "info", "--format", "{{.Host.Security.Rootless}}"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            WindowLog.log_error(f"Error checking podman rootless: {result.stderr}")
            return False
        return result.stdout.strip() == "true"
