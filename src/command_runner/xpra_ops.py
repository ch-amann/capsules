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

"""Xpra operations"""

import subprocess
import time

from .base import BaseCommandRunner, CommandResult
from utils import (
    get_xpra_socket_symlink_path, get_capsule_dir
)
from window_log import WindowLog

class XpraOps(BaseCommandRunner):
    def xpra_attach(self, capsule_name: str) -> CommandResult:
        """Attach xpra to capsule"""
        WindowLog.log_info(f"Xpra Attach: {capsule_name}")

        # Check xpra version
        try:
            result = self._run_command(["xpra", "--version"])
            if not result.success:
                return CommandResult(False, "Failed to get xpra version")
            if "v6." not in result.output:
                return CommandResult(False, f"Xpra version 6.x required. Found: {result.output}")
        except Exception as e:
            return CommandResult(False, f"Xpra not installed or not in PATH: {e}")

        # Setup directories and symlinks
        capsule_dir = get_capsule_dir(capsule_name)
        socket_path = get_xpra_socket_symlink_path(capsule_name)

        # Start xpra client in background
        log_file = capsule_dir / "xpra_client.log"
        if log_file.exists():
            log_file.unlink()

        try:
            subprocess.Popen(
                ["xpra", "attach", f"--title={capsule_name}", f"socket:{socket_path}"],
                stdout=open(log_file, "w"),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
        except Exception as e:
            return CommandResult(False, f"Failed to start xpra client: {e}")

        # Wait for connection
        timeout_s = 10
        step = 0.5
        while not self.xpra_is_attached(capsule_name) and timeout_s > 0:
            time.sleep(step)
            timeout_s -= step

        if timeout_s <= 0:
            return CommandResult(False, "Xpra attach timed out")

        return CommandResult(success=True)

    def xpra_detach(self, capsule_name: str) -> CommandResult:
        """Detach xpra from capsule"""
        socket_path = get_xpra_socket_symlink_path(capsule_name)
        result = self._run_command(["xpra", "detach", f"socket:{socket_path}"])
        if not result.success:
            return result

        timeout_s = 5
        step = 0.5
        while self.xpra_is_attached(capsule_name) and timeout_s > 0:
            time.sleep(step)
            timeout_s -= step
        if timeout_s <= 0:
            return CommandResult(False, "Xpra detach timed out")

        return result

    def xpra_is_attached(self, capsule_name: str) -> bool:
        """Check if xpra is attached to capsule"""
        try:
            result = subprocess.run(
                ["ss", "-x"],
                capture_output=True,
                text=True,
                check=True
            )
            return True if f"{capsule_name}_socket" in result.stdout else False
        except subprocess.SubprocessError:
            return False
