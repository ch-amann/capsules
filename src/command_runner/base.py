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

"""Base CommandRunner class with core functionality"""

import subprocess
from typing import List, Optional
from dataclasses import dataclass

from window_log import WindowLog
from settings import Settings

@dataclass
class CommandResult:
    """Result of a command execution"""
    success: bool
    error_message: Optional[str] = None
    output: Optional[str] = None

class BaseCommandRunner:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _run_command(
        self, 
        command: List[str], 
        check: bool = True, 
        capture_output: bool = True,
        log_output: bool = False
    ) -> CommandResult:
        """Execute a command and return standardized result"""
        try:
            if log_output:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                self._log_process_output(process)
                returncode = process.wait()
                if returncode != 0 and check:
                    raise subprocess.CalledProcessError(returncode, command)
                return CommandResult(success=True)
            else:
                result = subprocess.run(
                    command,
                    capture_output=capture_output,
                    text=True,
                    check=check
                )
                return CommandResult(
                    success=True,
                    output=result.stdout.strip() if capture_output else None
                )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            WindowLog.log_error(f"Command failed: {error_msg}")
            return CommandResult(success=False, error_message=error_msg)
        except Exception as e:
            WindowLog.log_error(f"Error executing command: {e}")
            return CommandResult(success=False, error_message=str(e))

    def _log_process_output(self, process: subprocess.Popen) -> None:
        """Log process output line by line"""
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                WindowLog.log_info(line.strip())