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

from dataclasses import dataclass
from typing import Dict, List
from PyQt6.QtWidgets import QMenu
from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QAction
from misc import Entity, ContainerStatus
from models import SelectedItem
from window_log import WindowLog

@dataclass
class MenuAction:
    name: str
    callback: str
    enabled_states: List[ContainerStatus] = None
    capsule_only: bool = False
    requires_running: bool = False

class ContextMenuHandler:
    def __init__(self, main_window):
        self.window = main_window
        self.actions: Dict[str, MenuAction] = {
            "Start": MenuAction(
                "Start",
                "start_container",
                [ContainerStatus.EXITED, ContainerStatus.CREATED]
            ),
            "Stop": MenuAction(
                "Stop",
                "stop_container",
                [ContainerStatus.RUNNING]
            ),
            "Restart": MenuAction(
                "Restart",
                "restart_container",
                [ContainerStatus.RUNNING]
            ),
            "Delete": MenuAction(
                "Delete",
                "delete_entity"
            ),
            "Terminal": MenuAction(
                "Terminal",
                "open_terminal",
                [ContainerStatus.RUNNING]
            ),
            "Execute Command": MenuAction(
                "Execute Command...",
                "execute_command",
                [ContainerStatus.RUNNING]
            ),
            "Open Shared Directory": MenuAction(
                "Open Shared Directory",
                "open_shared_directory"
            ),
            "Xpra Attach": MenuAction(
                "Xpra Attach",
                "attach_xpra",
                [ContainerStatus.RUNNING],
                capsule_only=True
            ),
            "Xpra Detach": MenuAction(
                "Xpra Detach",
                "detach_xpra",
                [ContainerStatus.RUNNING],
                capsule_only=True
            )
        }

    def _create_menu_action(self, menu: QMenu, action_key: str) -> QAction:
        """Create a menu action and connect its callback"""
        action_data = self.actions[action_key]
        action = menu.addAction(action_data.name)
        callback = getattr(self.window.callbacks, action_data.callback)
        action.triggered.connect(callback)
        return action

    def _should_enable_action(self, action_data: MenuAction, item: SelectedItem, status: ContainerStatus) -> bool:
        """Determine if an action should be enabled based on current state"""
        if self.window.uiDisabled:
            return False
            
        if action_data.capsule_only and item.type != Entity.CAPSULE:
            return False

        if action_data.enabled_states and status not in action_data.enabled_states:
            return False

        # Special case for Xpra actions
        if action_data.name == "Xpra Attach":
            return status == ContainerStatus.RUNNING and \
                   not self.window.command_runner.xpra_is_attached(item.getName())
        elif action_data.name == "Xpra Detach":
            return status == ContainerStatus.RUNNING and \
                   self.window.command_runner.xpra_is_attached(item.getName())

        # Always enable Delete and Open Shared Directory
        if action_data.name in ["Delete", "Open Shared Directory"]:
            return True

        return True

    def show_context_menu(self, position: QPoint):
        sender_tree = self.window.sender()
        index = sender_tree.indexAt(position)
        if not index.isValid():
            return

        # Get item info
        item_type = Entity.TEMPLATE if sender_tree == self.window.templates_tree else Entity.CAPSULE
        item_data = [
            sender_tree.model().item(index.row(), col).text()
            for col in range(sender_tree.model().columnCount())
        ]
        right_clicked_item = SelectedItem(item_type, item_data)
        status = right_clicked_item.getStatus()

        # Create menu and actions
        context_menu = QMenu(self.window)
        menu_actions = {}
        
        # Add all actions to menu
        for action_key in self.actions:
            menu_actions[action_key] = self._create_menu_action(context_menu, action_key)
            
        # Enable/disable actions based on state
        for action_key, action in menu_actions.items():
            action.setEnabled(
                self._should_enable_action(self.actions[action_key], right_clicked_item, status)
            )

        WindowLog.log_debug(f"Right-clicked on {right_clicked_item}")
        context_menu.exec(sender_tree.viewport().mapToGlobal(position))
