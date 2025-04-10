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

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QComboBox, QLabel
from typing import Optional

from .validators import HostPortValidator, ContainerPortValidator

class PortMappingWidget(QWidget):
    """Widget for host:container port mapping entry"""
    MIN_HOST_PORT = 1024
    MIN_CONTAINER_PORT = 1
    MAX_PORT = 65535

    def __init__(self, parent=None, on_change=None):
        super().__init__(parent)
        self.on_change = on_change
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.host_port = QLineEdit()
        self.host_port.setPlaceholderText("Host (>1024)")
        self.host_port.setMaximumWidth(100)
        self.host_port.setValidator(HostPortValidator(self.MIN_HOST_PORT, self.MAX_PORT))
        self.host_port.textChanged.connect(self._on_text_changed)
        
        self.container_port = QLineEdit()
        self.container_port.setPlaceholderText("Container")
        self.container_port.setMaximumWidth(100)
        self.container_port.setValidator(ContainerPortValidator(self.MIN_CONTAINER_PORT, self.MAX_PORT))
        self.container_port.textChanged.connect(self._on_text_changed)
        
        self.protocol = QComboBox()
        self.protocol.addItems(["tcp", "udp"])
        self.protocol.setMaximumWidth(70)
        
        layout.addWidget(self.host_port)
        layout.addWidget(QLabel(":"))
        layout.addWidget(self.container_port)
        layout.addWidget(self.protocol)
        layout.addStretch()
        
        self.setLayout(layout)

    def _on_text_changed(self):
        """Notify parent when port values change"""
        if self.on_change:
            self.on_change()

    def is_valid(self) -> bool:
        """Check if both ports are valid or both empty"""
        host = self.host_port.text().strip()
        container = self.container_port.text().strip()
        
        if not host and not container:
            return True
        if not host or not container:
            return False
            
        try:
            host_num = int(host)
            container_num = int(container)
            return (self.MIN_HOST_PORT <= host_num <= self.MAX_PORT and 
                   self.MIN_CONTAINER_PORT <= container_num <= self.MAX_PORT)
        except ValueError:
            return False
    
    def get_mapping(self) -> Optional[str]:
        """Return port mapping as 'host:container/protocol' if both filled, None if both empty"""
        host = self.host_port.text().strip()
        container = self.container_port.text().strip()
        
        if host and container:
            protocol = self.protocol.currentText()
            return f"{host}:{container}/{protocol}"
        return None