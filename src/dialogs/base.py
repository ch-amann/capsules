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

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QDialogButtonBox, 
    QRadioButton, QWidget
)
from PyQt6.QtCore import Qt
from typing import List

class BaseDialog(QDialog):
    """Base dialog class with common functionality"""
    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.port_mappings = []
        self.port_layout = None
        
        # Create button box and store OK button early
        self.button_box = self._create_button_box()
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)

    def _create_button_box(self) -> QDialogButtonBox:
        """Create standard OK/Cancel button box"""
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        return button_box

    def _create_network_buttons(self) -> QHBoxLayout:
        """Create network enable/disable radio buttons"""
        network_layout = QHBoxLayout()
        self.network_enabled = QRadioButton("enabled")
        self.network_disabled = QRadioButton("disabled")
        self.network_enabled.setChecked(True)
        network_layout.addWidget(self.network_enabled)
        network_layout.addWidget(self.network_disabled)
        network_layout.addStretch()
        return network_layout

    def _create_network_section(self) -> QWidget:
        """Create network section with enable/disable"""
        section = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        network_buttons = self._create_network_buttons()
        layout.addLayout(network_buttons)
        section.setLayout(layout)
        return section

    def get_port_mappings(self) -> List[str]:
        """Get all valid port mappings if network is enabled"""
        if not self.network_enabled.isChecked():
            return []
        return [m.get_mapping() for m in self.port_mappings 
                if m.get_mapping() is not None]