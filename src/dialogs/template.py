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

from PyQt6.QtWidgets import QFormLayout, QLineEdit, QComboBox
from typing import List

from .base import BaseDialog
from .validators import NameValidator
from .results import TemplateResult

class AddTemplateDialog(BaseDialog):
    def __init__(self, parent, existing_names: List[str], base_images: List[str]):
        super().__init__(parent, "Add Template")
        self._init_ui(existing_names, base_images)

    def _init_ui(self, existing_names: List[str], base_images: List[str]):
        layout = QFormLayout()
        
        # Create input fields with validation
        self.name_input = QLineEdit()
        self.name_input.setValidator(NameValidator())
        self.name_input.textChanged.connect(self._validate_input)
        self.base_image_combo = QComboBox()
        self.base_image_combo.addItems(base_images)

        # Create network section
        network_section = self._create_network_section()

        # Add fields to layout
        layout.addRow("Template Name:", self.name_input)
        layout.addRow("Base Image:", self.base_image_combo)
        layout.addRow("Network:", network_section)
        layout.addRow(self.button_box)
        
        self._validate_input()
        self.setLayout(layout)

    def _validate_input(self):
        """Enable OK button only if name is valid"""
        name = self.name_input.text().strip()
        valid = bool(name and ' ' not in name)
        self.ok_button.setEnabled(valid)

    def get_data(self) -> TemplateResult:
        return TemplateResult(
            name=self.name_input.text(),
            base_image=self.base_image_combo.currentText(),
            network_enabled=self.network_enabled.isChecked()
        )