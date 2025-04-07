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
Data models for Capsules application.
Defines the core data structures for templates, capsules and selection handling.
"""

from dataclasses import dataclass
from typing import List, Union
from misc import ContainerStatus, Entity

@dataclass
class Template:
    """Represents a container template configuration"""
    name: str
    base_image: str
    status: ContainerStatus
    network: str

    def __str__(self) -> str:
        return f"{self.name} - {self.base_image} - {self.status}"

@dataclass
class Capsule:
    """Represents a container instance based on a template"""
    name: str
    template_name: str
    status: ContainerStatus
    network: str
    xpra_attached: bool

    def __str__(self) -> str:
        return f"{self.name} - {self.template_name} - {self.status}"

class SelectedItem:
    """
    Represents a selected item in the UI.
    Handles conversion of raw data to Template/Capsule objects.
    """
    def __init__(self, type: Entity, data: List[str]):
        """
        Initialize selected item
        Args:
            type: Entity type (TEMPLATE or CAPSULE)
            data: List of strings containing item data
                 [name, base/template, status, network, xpra(optional)]
        """
        self.type = type
        self.data = data

    def __str__(self) -> str:
        return f"{self.type} - {self.data}"

    def getName(self) -> str:
        """Get item name (first column)"""
        return self.data[0]

    def getStatus(self) -> ContainerStatus:
        """Get container status (third column)"""
        try:
            return ContainerStatus.from_str(self.data[2].lower())
        except (ValueError, IndexError):
            return ContainerStatus.UNKNOWN

    def getNetwork(self) -> str:
        """Get network configuration (fourth column)"""
        try:
            return self.data[3]
        except IndexError:
            return "unknown"

    def toTemplate(self) -> Template:
        """Convert to Template object"""
        if self.type != Entity.TEMPLATE:
            raise ValueError("Cannot convert non-template item to Template")
        return Template(
            name=self.getName(),
            base_image=self.data[1],
            status=self.getStatus(),
            network=self.getNetwork()
        )

    def toCapsule(self) -> Capsule:
        """Convert to Capsule object"""
        if self.type != Entity.CAPSULE:
            raise ValueError("Cannot convert non-capsule item to Capsule")
        return Capsule(
            name=self.getName(),
            template_name=self.data[1],
            status=self.getStatus(),
            network=self.getNetwork(),
            xpra_attached=self.data[4] == "Yes" if len(self.data) > 4 else False
        )

    def toEntity(self) -> Union[Template, Capsule]:
        """Convert to appropriate entity type based on self.type"""
        return self.toTemplate() if self.type == Entity.TEMPLATE else self.toCapsule()