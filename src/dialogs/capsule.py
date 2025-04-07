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
    QFormLayout, QLineEdit, QComboBox, QLabel, 
    QVBoxLayout, QPushButton, QHBoxLayout, QWidget
)
from typing import List

from .base import BaseDialog
from .validators import NameValidator
from .results import CapsuleResult
from .port_mapping import PortMappingWidget

class AddCapsuleDialog(BaseDialog):
    def __init__(self, parent, existing_names: List[str], template_names: List[str]):
        super().__init__(parent, "Add Capsule")
        self._init_ui(existing_names, template_names)

    def _init_ui(self, existing_names: List[str], template_names: List[str]):
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setValidator(NameValidator())
        self.name_input.textChanged.connect(self._validate_all)
        self.template_combo = QComboBox()
        self.template_combo.addItems(template_names)

        network_section = self._create_network_section()

        ports_widget = QWidget()
        ports_layout = QVBoxLayout()
        ports_layout.setContentsMargins(0, 0, 0, 0)
        
        self.port_layout = ports_layout
        self._add_port_mapping()
        
        button_container = QHBoxLayout()
        add_button = QPushButton("+")
        add_button.setMaximumWidth(30)
        add_button.clicked.connect(self._add_port_mapping)
        button_container.addWidget(add_button)
        button_container.addStretch()
        ports_layout.addLayout(button_container)
        
        ports_widget.setLayout(ports_layout)
        ports_widget.setVisible(self.network_enabled.isChecked())

        ports_label = QLabel("Ports:")
        ports_label.setVisible(self.network_enabled.isChecked())
        
        layout.addRow("Capsule Name:", self.name_input)
        layout.addRow("Template:", self.template_combo)
        layout.addRow("Network:", network_section)
        layout.addRow(ports_label, ports_widget)
        layout.addRow(self.button_box)
        
        def update_ports_visibility(enabled: bool):
            ports_widget.setVisible(enabled)
            ports_label.setVisible(enabled)
            self._validate_ports()
        
        self.network_enabled.toggled.connect(update_ports_visibility)
        update_ports_visibility(self.network_enabled.isChecked())
        
        self.setLayout(layout)
        self._validate_all()

    def _add_port_mapping(self):
        mapping = PortMappingWidget(on_change=self._validate_ports)
        self.port_mappings.append(mapping)
        self.port_layout.insertWidget(len(self.port_mappings) - 1, mapping)
        self._validate_ports()

    def _validate_ports(self):
        """Validate port mappings if network is enabled"""
        if not self.network_enabled.isChecked():
            # When network is disabled, ports don't matter
            self._validate_all(port_valid=True)
            return

        # When network is enabled, check all port mappings
        all_valid = all(mapping.is_valid() for mapping in self.port_mappings)
        self._validate_all(port_valid=all_valid)

    def _validate_all(self, port_valid: bool = True):
        """Validate both name and ports"""
        name = self.name_input.text().strip()
        name_valid = bool(name and ' ' not in name)
        
        # Enable OK button only if both name and ports are valid
        self.ok_button.setEnabled(bool(name_valid and port_valid))

    def get_data(self) -> CapsuleResult:
        return CapsuleResult(
            name=self.name_input.text(),
            template=self.template_combo.currentText(),
            network_enabled=self.network_enabled.isChecked(),
            port_mappings=self.get_port_mappings()
        )