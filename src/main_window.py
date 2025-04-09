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
Main window implementation for Capsules application.
Handles UI layout, events, and state management.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Callable
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTreeView, 
    QPushButton, QTextEdit, QMenu, QLabel, QSystemTrayIcon, QComboBox,
    QHeaderView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QCloseEvent, QIcon
from PyQt6.QtCore import Qt, QEvent

from window_log import WindowLog, WindowLogLevel
from misc import Entity, ContainerStatus, CapsulesDir, TemplateDir
from models import SelectedItem
from callbacks import GuiCallbacks
from context_menu import ContextMenuHandler
from command_runner import CommandRunner
from settings import Settings

@dataclass
class TreeConfig:
    """Configuration for tree views"""
    name: str
    headers: List[str]
    min_height: int = 150
    section_size: int = 140

@dataclass
class ButtonConfig:
    """Configuration for action buttons"""
    label: str
    callback_name: str
    always_enabled: bool = False

class ShowWindowEvent(QEvent):
    """Custom event for window activation"""
    EventType = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self):
        super().__init__(self.EventType)

class MainWindow(QMainWindow):
    def __init__(self, app: QApplication, icon: QIcon):
        super().__init__()
        self.app = app
        self.icon = icon
        self.uiDisabled = False
        self.buttons: Dict[str, QPushButton] = {}  # Initialize buttons dict
        
        # Initialize core components
        self._init_core_components()
        # Set up UI
        self._setup_ui()

    def _init_core_components(self) -> None:
        """Initialize core application components"""
        # Create required directories
        CapsulesDir.mkdir(parents=True, exist_ok=True)
        TemplateDir.mkdir(parents=True, exist_ok=True)

        # Set window properties
        self.setWindowTitle("Capsules")
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setGeometry(100, 100, 800, 400)

        # Initialize components
        WindowLog.init(self.append_log_message, WindowLogLevel.INFO)
        self.settings = Settings()
        self.command_runner = CommandRunner(self.settings)
        self.callbacks = GuiCallbacks(self, self.command_runner, self.enableUi)
        self.context_menu = ContextMenuHandler(self)

    def _setup_ui(self) -> None:
        """Set up the main window UI layout"""
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Create and setup UI sections
        self._setup_tray_icon()
        self._setup_button_bar()
        self._setup_trees()
        self._setup_logs_section()

        # Assemble main layout
        main_layout.addLayout(self.button_layout)
        main_layout.addWidget(self.trees_widget)
        main_layout.addWidget(self.logs_widget)

        # Set central widget
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Initial UI state
        self.refresh_view()
        self._disable_action_buttons()
        WindowLog.log_info("Application start complete")
        if not self.command_runner.podman_allows_rootless():
            WindowLog.log_error("Podman rootless mode not supported on this system!")
            self.disableUi()

    def _setup_tray_icon(self) -> None:
        """Set up system tray icon and menu"""
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icon)
        self.tray.setToolTip("Capsules")
        self.tray.activated.connect(self._on_tray_activated)
        
        tray_menu = QMenu()
        tray_menu.addAction("Show").triggered.connect(self.show)
        tray_menu.addAction("Exit").triggered.connect(self.app.quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.setVisible(not self.isVisible())

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event - minimize to tray instead"""
        event.ignore()
        self.hide()

    def event(self, event: QEvent) -> bool:
        """Handle custom events"""
        if event.type() == ShowWindowEvent.EventType:
            self.show()
            self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
            self.raise_()
            self.activateWindow()
            return True
        return super().event(event)

    def _setup_button_bar(self) -> None:
        """Set up action button bar"""
        self.button_layout = QHBoxLayout()
        self.buttons: Dict[str, QPushButton] = {}

        button_configs = [
            ButtonConfig("Add Template", "add_template", True),
            ButtonConfig("Add Capsule", "add_capsule", True),
            ButtonConfig("Start", "start_container"),
            ButtonConfig("Stop", "stop_container"),
            ButtonConfig("Restart", "restart_container"),
            ButtonConfig("Delete", "delete_entity"),
            ButtonConfig("Terminal", "open_terminal"),
            ButtonConfig("Xpra Attach", "attach_xpra"),
            ButtonConfig("Xpra Detach", "detach_xpra"),
            ButtonConfig("Refresh", "refresh", True)
        ]

        for config in button_configs:
            button = QPushButton(config.label)
            if config.callback_name == "refresh":
                # Special case for refresh button
                button.clicked.connect(self.refresh_view)
            else:
                # All other buttons use GuiCallbacks
                callback = getattr(self.callbacks, config.callback_name)
                button.clicked.connect(callback)
            self.buttons[config.callback_name] = button
            self.button_layout.addWidget(button)

    def _setup_trees(self) -> None:
        """Set up template and capsule tree views in vertical arrangement"""
        self.trees_widget = QWidget()
        trees_layout = QVBoxLayout()

        # Templates section
        templates_section = QWidget()
        templates_layout = QVBoxLayout()
        templates_layout.addWidget(QLabel("Templates"))
        self.templates_tree, self.templates_model = self._create_tree_view(TreeConfig(
            "Templates",
            ["Name", "Base Image", "Status", "Network"]
        ))
        templates_layout.addWidget(self.templates_tree)
        templates_section.setLayout(templates_layout)

        # Capsules section
        capsules_section = QWidget()
        capsules_layout = QVBoxLayout()
        capsules_layout.addWidget(QLabel("Capsules"))
        self.capsules_tree, self.capsules_model = self._create_tree_view(TreeConfig(
            "Capsules",
            ["Name", "Template", "Status", "Network", "Ports", "Xpra Attached"]
        ))
        capsules_layout.addWidget(self.capsules_tree)
        capsules_section.setLayout(capsules_layout)

        # Add both sections to main layout
        trees_layout.addWidget(templates_section)
        trees_layout.addWidget(capsules_section)
        self.trees_widget.setLayout(trees_layout)

        # Connect selection changes
        self.templates_tree.selectionModel().selectionChanged.connect(self._on_template_selected)
        self.capsules_tree.selectionModel().selectionChanged.connect(self._on_capsule_selected)

    def _create_tree_view(self, config: TreeConfig) -> Tuple[QTreeView, QStandardItemModel]:
        """Create and configure a tree view"""
        tree = QTreeView()
        model = QStandardItemModel()
        
        # Setup model and view
        model.setHorizontalHeaderLabels(config.headers)
        tree.setModel(model)
        tree.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        tree.setSortingEnabled(True)
        tree.setMinimumHeight(config.min_height)
        
        # Setup context menu
        tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(self.context_menu.show_context_menu)
        
        # Configure header
        header = tree.header()
        header.setDefaultSectionSize(config.section_size)
        header.setSortIndicatorShown(True)
        
        # Set default sorting to ascending by name (column 0)
        tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        
        return tree, model

    def _setup_logs_section(self) -> None:
        """Set up logs section with text box and level selector"""
        self.logs_widget = QWidget()
        logs_layout = QVBoxLayout()
        
        # Create header with label and dropdown
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Logs"))
        
        self.log_level_dropdown = QComboBox()
        self.log_level_dropdown.addItems([level.name.capitalize() for level in WindowLogLevel])
        self.log_level_dropdown.setCurrentText(WindowLogLevel.INFO.name.capitalize())
        self.log_level_dropdown.currentTextChanged.connect(self._on_log_level_changed)
        
        header_layout.addWidget(self.log_level_dropdown)
        header_layout.addStretch()
        
        # Create logs text box
        self.logs_textbox = QTextEdit()
        self.logs_textbox.setReadOnly(True)
        self.logs_textbox.setMinimumHeight(200)
        
        logs_layout.addLayout(header_layout)
        logs_layout.addWidget(self.logs_textbox)
        self.logs_widget.setLayout(logs_layout)

    def _disable_action_buttons(self) -> None:
        """Disable all action buttons except core functionality"""
        for button in self.buttons.values():
            button.setEnabled(False)
        
        # Always keep these enabled
        always_enabled = ['add_template', 'add_capsule', 'refresh']
        for name in always_enabled:
            self.buttons[name].setEnabled(True)

    def _update_button_states(self, item: SelectedItem) -> None:
        """Update button states based on container status and type"""
        self._disable_action_buttons()
        
        if not item:
            return
            
        status = item.getStatus()
        name = item.getName()
        
        # Enable delete for all states
        self.buttons['delete_entity'].setEnabled(True)
        
        if status == ContainerStatus.RUNNING:
            self.buttons['stop_container'].setEnabled(True)
            self.buttons['restart_container'].setEnabled(True)
            self.buttons['open_terminal'].setEnabled(True)
            
            if item.type == Entity.CAPSULE:
                is_attached = self.command_runner.xpra_is_attached(name)
                self.buttons['attach_xpra'].setEnabled(not is_attached)
                self.buttons['detach_xpra'].setEnabled(is_attached)
                
        elif status in [ContainerStatus.EXITED, ContainerStatus.CREATED]:
            self.buttons['start_container'].setEnabled(True)

    def refresh_view(self) -> None:
        """Refresh both tree views and maintain selection and sorting"""
        # Store current state
        selected_item = self.get_selected_item()
        templates_sort = (
            self.templates_tree.header().sortIndicatorSection(),
            self.templates_tree.header().sortIndicatorOrder()
        )
        capsules_sort = (
            self.capsules_tree.header().sortIndicatorSection(),
            self.capsules_tree.header().sortIndicatorOrder()
        )

        # Clear models
        self.templates_model.removeRows(0, self.templates_model.rowCount())
        self.capsules_model.removeRows(0, self.capsules_model.rowCount())

        # Update trees
        self._update_templates_tree()
        self._update_capsules_tree()

        # Restore sorting
        self.templates_tree.sortByColumn(*templates_sort)
        self.capsules_tree.sortByColumn(*capsules_sort)

        # Restore selection
        if selected_item:
            self.set_selected_item(selected_item)

    def _update_templates_tree(self) -> None:
        """Update templates tree with current data"""
        templates = self.command_runner.get_existing_templates()
        
        for template in templates:
            row_data = [template.name, template.base_image, template.status.value, template.network]
            row_items = [QStandardItem(str(item)) for item in row_data]
            
            for item in row_items:
                item.setEditable(False)
            self.templates_model.appendRow(row_items)

    def _update_capsules_tree(self) -> None:
        """Update capsules tree with current data"""
        capsules = self.command_runner.get_existing_capsules()
        
        for capsule in capsules:
            xpra_attached = "Yes" if capsule.xpra_attached else "No"
            row_data = [capsule.name, capsule.template, capsule.status.value, capsule.network, capsule.ports, xpra_attached]
            row_items = [QStandardItem(str(item)) for item in row_data]
            
            for item in row_items:
                item.setEditable(False)
            self.capsules_model.appendRow(row_items)

    def append_log_message(self, color: str, message: str) -> None:
        """Append a colored message to the log text box"""
        html_message = f'<span style="color: {color};">{message}</span>'
        self.logs_textbox.append(html_message)
        scrollbar = self.logs_textbox.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_log_level_changed(self, level_name: str) -> None:
        """Handle log level change"""
        level = WindowLogLevel[level_name.upper()]
        WindowLog.log_force(f"Log level changed to {level_name}")
        WindowLog.set_log_level(level)

    def disableUi(self) -> None:
        """Disable all UI elements during operations"""
        for button in self.buttons.values():
            button.setEnabled(False)
        self.uiDisabled = True
        
    def enableUi(self) -> None:
        """Re-enable basic buttons and refresh UI after operations"""
        # First refresh views to get latest state
        self.refresh_view()
        
        # Then re-enable buttons based on new state
        self.buttons['add_template'].setEnabled(True)
        self.buttons['add_capsule'].setEnabled(True)
        self.buttons['refresh'].setEnabled(True)
        self.uiDisabled = False
        
        # Update button states based on current selection
        item = self.get_selected_item()
        if item:
            self._update_button_states(item)

    def _on_template_selected(self) -> None:
        """Handle template selection"""
        # Clear capsule selection when template is selected
        if self.templates_tree.selectionModel().hasSelection():
            self.capsules_tree.selectionModel().clearSelection()
        
        item = self.get_selected_item()
        if not item or item.type != Entity.TEMPLATE:
            return

        self._update_button_states(item)

    def _on_capsule_selected(self) -> None:
        """Handle capsule selection"""
        # Clear template selection when capsule is selected
        if self.capsules_tree.selectionModel().hasSelection():
            self.templates_tree.selectionModel().clearSelection()
        
        item = self.get_selected_item()
        if not item or item.type != Entity.CAPSULE:
            return

        self._update_button_states(item)

    def get_selected_item(self) -> Optional[SelectedItem]:
        """Get currently selected item from either tree"""
        # Check templates tree first
        if self.templates_tree.selectionModel().hasSelection():
            index = self.templates_tree.selectionModel().currentIndex()
            model = self.templates_model
            item_type = Entity.TEMPLATE
        # Then check capsules tree
        elif self.capsules_tree.selectionModel().hasSelection():
            index = self.capsules_tree.selectionModel().currentIndex()
            model = self.capsules_model
            item_type = Entity.CAPSULE
        else:
            return None

        item_data = [
            model.item(index.row(), col).text()
            for col in range(model.columnCount())
        ]

        return SelectedItem(item_type, item_data)

    def set_selected_item(self, item: Optional[SelectedItem]) -> None:
        """Set selection in appropriate tree view"""
        if not item:
            return
            
        # Determine which tree and model to use
        tree = self.templates_tree if item.type == Entity.TEMPLATE else self.capsules_tree
        model = self.templates_model if item.type == Entity.TEMPLATE else self.capsules_model
        
        # Find items matching the name in first column
        items = model.findItems(item.getName(), Qt.MatchFlag.MatchExactly)
        
        # Set selection if item was found
        if items:
            tree.setCurrentIndex(items[0].index())
            self._update_button_states(item)
