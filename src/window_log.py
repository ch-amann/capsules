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
Logging functionality for the Capsules application.
Provides a window-based logging system with different log levels and colors.
"""

from enum import Enum, auto
from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass

from worker import LogWorker

class WindowLogLevel(Enum):
    """Log levels ordered by severity"""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    NONE = auto()

@dataclass
class LogConfig:
    """Configuration for log messages"""
    color: str
    level: WindowLogLevel

class WindowLog:
    """Static logging class for the application"""
    _is_init: bool = False
    _log_level: WindowLogLevel = WindowLogLevel.INFO
    _worker: Optional[LogWorker] = None

    # Color configuration for different log levels
    _log_configs: Dict[str, LogConfig] = {
        'force':   LogConfig('regular',  WindowLogLevel.NONE),
        'debug':   LogConfig('gray',   WindowLogLevel.DEBUG),
        'info':    LogConfig('regular',  WindowLogLevel.INFO),
        'warning': LogConfig('orange', WindowLogLevel.WARNING),
        'error':   LogConfig('red',    WindowLogLevel.ERROR)
    }

    @classmethod
    def init(cls, log_signal_handler, log_level: WindowLogLevel) -> None:
        """Initialize the logging system"""
        if cls._is_init:
            return
        cls._log_level = log_level
        cls._worker = LogWorker(log_signal_handler)
        cls._is_init = True

    @classmethod
    def set_log_level(cls, log_level: WindowLogLevel) -> None:
        """Change the current log level"""
        if not cls._is_init:
            raise RuntimeError("Logging system not initialized")
        cls._log_level = log_level

    @classmethod
    def _format_message(cls, message: str) -> str:
        """Format a log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] {message}"

    @classmethod
    def _log(cls, message: str, config: LogConfig) -> None:
        """Internal logging method"""
        if not cls._is_init:
            raise RuntimeError("Logging system not initialized")
            
        if cls._log_level.value <= config.level.value:
            formatted_message = cls._format_message(message)
            print(formatted_message)
            cls._worker.add_log(config.color, formatted_message)

    # Public logging methods
    @classmethod
    def log_force(cls, message: str) -> None:
        """Log a message regardless of the current log level"""
        cls._log(message, cls._log_configs['force'])

    @classmethod
    def log_debug(cls, message: str) -> None:
        """Log a debug message"""
        cls._log(message, cls._log_configs['debug'])

    @classmethod
    def log_info(cls, message: str) -> None:
        """Log an informational message"""
        cls._log(message, cls._log_configs['info'])

    @classmethod
    def log_warning(cls, message: str) -> None:
        """Log a warning message"""
        cls._log(message, cls._log_configs['warning'])

    @classmethod
    def log_error(cls, message: str) -> None:
        """Log an error message"""
        cls._log(message, cls._log_configs['error'])