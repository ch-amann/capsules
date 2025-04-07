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

"""Container operations"""

from typing import List
from .base import BaseCommandRunner, CommandResult
from misc import Entity, ContainerStatus
from utils import CapsulesDir, TemplateDir

class ContainerOps(BaseCommandRunner):
    def fetch_entities(self, entity_type: Entity) -> List[str]:
        """Get list of existing entities"""
        directory = CapsulesDir if entity_type == Entity.CAPSULE else TemplateDir
        return [
            entity.name 
            for entity in directory.iterdir() 
            if entity.is_dir()
        ]

    def get_container_status(self, container_name: str) -> ContainerStatus:
        """Get current status of a container"""
        result = self._run_command([
            "podman", "inspect",
            "--format={{.State.Status}}",
            container_name
        ])
        if not result.success or not result.output:
            return ContainerStatus.UNKNOWN
        return ContainerStatus[result.output.upper()]

    def get_container_network(self, container_name: str) -> str:
        """Get network mode of a container"""
        result = self._run_command([
            "podman", "inspect",
            "--format={{.HostConfig.NetworkMode}}",
            container_name
        ])
        return result.output if result.success else "unknown"

    def get_container_ports(self, container_name: str) -> str:
        """Get forwarded ports of a container (single string: <host>-><container>/<protocol>  ...)"""
        result = self._run_command([
            "podman", "inspect",
            "--format={{range $key, $val := .NetworkSettings.Ports}}{{range $val}}{{.HostPort}}->{{$key}}  {{end}}{{end}}",
            container_name
        ])
        return result.output if result.success else ""

    def start_container(self, container_name: str) -> CommandResult:
        """Start a container"""
        return self._run_command(["podman", "start", container_name])

    def stop_container(self, container_name: str) -> CommandResult:
        """Stop a container"""
        return self._run_command(["podman", "stop", container_name])

    def stop_container_immediately(self, container_name: str) -> CommandResult:
        """Stop a container"""
        return self._run_command(["podman", "stop", "--time", "0", container_name])

    def restart_container(self, container_name: str) -> CommandResult:
        """Restart a container"""
        return self._run_command(["podman", "restart", container_name])
    
    def restart_container_immediately(self, container_name: str) -> CommandResult:
        """Restart a container"""
        return self._run_command(["podman", "restart", "--time", "0", container_name])