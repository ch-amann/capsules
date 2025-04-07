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
Miscellaneous definitions and utilities for Capsules.
Contains path definitions, enums and other common structures.
"""

from enum import Enum, auto
from pathlib import Path
from typing import Final

# Application directories
# These are constants that should not be modified after initialization
UserAppDir: Final[Path] = Path.home() / ".capsules"
CapsulesDir: Final[Path] = UserAppDir / "capsules"
TemplateDir: Final[Path] = UserAppDir / "templates"
ProjectBaseDir: Final[Path] = Path(__file__).parent.resolve() / ".."

class ContainerStatus(Enum):
    """
    Represents the possible states of a container.
    Maps directly to podman container states.
    """
    RUNNING = "running"
    CREATED = "created"
    EXITED = "exited"
    PAUSED = "paused"
    RESTARTING = "restarting"
    DEAD = "dead"
    UNKNOWN = "unknown"

    @classmethod
    def from_str(cls, status_str: str) -> 'ContainerStatus':
        """
        Convert a string to ContainerStatus enum.
        Returns UNKNOWN if status string is not recognized.
        """
        try:
            return cls(status_str.lower())
        except ValueError:
            return cls.UNKNOWN

class Entity(Enum):
    """
    Represents the type of container entity.
    Used to distinguish between templates and capsules.
    """
    TEMPLATE = auto()
    CAPSULE = auto()

    def __str__(self) -> str:
        return self.name.lower()
