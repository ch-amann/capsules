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

from PyQt6.QtWidgets import QVBoxLayout, QLabel, QLineEdit

from .base import BaseDialog

class DeleteConfirmationDialog(BaseDialog):
    def __init__(self, parent, entity_name: str):
        super().__init__(parent, "Confirm Delete")
        self._init_ui(entity_name)

    def _init_ui(self, entity_name: str):
        layout = QVBoxLayout()
        message = f"Are you sure you want to delete '{entity_name}'?"
        layout.addWidget(QLabel(message))
        layout.addWidget(self.button_box)
        self.setLayout(layout)

class ExecuteCommandDialog(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, "Execute Command")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command to execute...")
        layout.addWidget(self.command_input)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_command(self) -> str:
        return self.command_input.text().strip()