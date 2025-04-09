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

from PyQt6.QtWidgets import QDialog
from enum import Enum
from misc import Entity, ContainerStatus
from dialogs import AddTemplateDialog, AddCapsuleDialog, DeleteConfirmationDialog, ExecuteCommandDialog
from worker import CommandWorker
from command_runner import CommandRunner
from window_log import WindowLog
from typing import Optional, Tuple, List

class CallbackResult(Enum):
    SUCCESS = "Done!"
    FAILED_TEMPLATE = "Failed to create template"
    FAILED_CAPSULE = "Failed to create capsule"
    FAILED_DELETE_TEMPLATE = "Failed to delete template"
    FAILED_DELETE_CAPSULE = "Failed to delete capsule"

class GuiCallbacks:
    def __init__(self, main_window, command_runner: CommandRunner, command_done_signal_handler):
        self.window = main_window
        self.command_runner = command_runner
        self.worker = CommandWorker(command_done_signal_handler)

    def _get_names_from_model(self, model) -> List[str]:
        return [model.item(i, 0).text() for i in range(model.rowCount())]

    def _handle_dialog_result(self, dialog: QDialog, operation_name: str) -> Optional[Tuple]:
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog.get_data()

    def _execute_background_task(self, task, *args):
        self.window.disableUi()
        self.worker.execute_function(task, *args)

    # Template operations
    def add_template(self):
        WindowLog.log_debug("Add Template button clicked")
        template_names = self._get_names_from_model(self.window.templates_model)
        base_images = self.command_runner.get_available_base_images()
        
        dialog_result = self._handle_dialog_result(
            AddTemplateDialog(self.window, template_names, base_images),
            "template creation"
        )
        if not dialog_result:
            return

        name = dialog_result.name
        base_image = dialog_result.base_image
        network_enabled = dialog_result.network_enabled

        if not self.command_runner.validate_name(name, template_names, "Template"):
            return

        WindowLog.log_info(f"Creating template '{name}' with base image '{base_image}'...")
        self._execute_background_task(self.__add_template_background_task, 
                                   name, base_image, network_enabled)

    def __add_template_background_task(self, name: str, base_image: str, network_enabled: bool):
        result = self.command_runner.create_template(name, base_image, network_enabled)
        if not result.success:
            WindowLog.log_error(CallbackResult.FAILED_TEMPLATE.value)
            WindowLog.log_error(result.error_message)
        else:
            WindowLog.log_info(CallbackResult.SUCCESS.value)

    # Capsule operations
    def add_capsule(self):
        WindowLog.log_debug("Add Capsule button clicked")
        capsule_names = self._get_names_from_model(self.window.capsules_model)
        template_names = self._get_names_from_model(self.window.templates_model)
        
        dialog_result = self._handle_dialog_result(
            AddCapsuleDialog(self.window, capsule_names, template_names),
            "capsule creation"
        )
        if not dialog_result:
            return

        name = dialog_result.name
        template_name = dialog_result.template
        network_enabled = dialog_result.network_enabled
        port_mappings = dialog_result.port_mappings

        if not self.command_runner.validate_name(name, capsule_names, "Capsule"):
            return

        WindowLog.log_info(f"Creating capsule '{name}' with template '{template_name}'...")
        self._execute_background_task(self.__add_capsule_background_task, 
                                   name, template_name, network_enabled, port_mappings)

    def __add_capsule_background_task(self, name: str, template_name: str, network_enabled: bool, port_mappings: List[str]):
        result = self.command_runner.create_capsule(name, template_name, network_enabled, port_mappings)
        if not result.success:
            WindowLog.log_error(CallbackResult.FAILED_CAPSULE.value)
            WindowLog.log_error(result.error_message)
        else:
            WindowLog.log_info(CallbackResult.SUCCESS.value)

    # Container operations
    def start_container(self):
        item = self.window.get_selected_item()
        if not item:
            return
        
        name = item.getName()
        WindowLog.log_info(f"Start: {name}")
        self._execute_background_task(self.__start_container_background_task, name)

    def __start_container_background_task(self, name: str):
        result = self.command_runner.start_container(name)
        if not result.success:
            WindowLog.log_error(result.error_message)

    def stop_container(self):
        item = self.window.get_selected_item()
        if not item:
            return
        
        name = item.getName()
        WindowLog.log_info(f"Stop: {name}")
        self._execute_background_task(self.__stop_container_background_task, item.type, name)

    def __stop_container_background_task(self, container_type: Entity, name: str):
        if container_type == Entity.CAPSULE and self.command_runner.xpra_is_attached(name):
            result = self.command_runner.xpra_detach(name)
            if not result.success:
                WindowLog.log_error(result.error_message)

        result = self.command_runner.stop_container_immediately(name)
        if not result.success:
            WindowLog.log_error(result.error_message)

    def restart_container(self):
        item = self.window.get_selected_item()
        if not item:
            return
        
        name = item.getName()
        WindowLog.log_info(f"Restart: {name}")
        self._execute_background_task(self.__restart_container_background_task, item.type, name)

    def __restart_container_background_task(self, container_type: Entity, name: str):
        if container_type == Entity.CAPSULE and self.command_runner.xpra_is_attached(name):
            self.command_runner.xpra_detach(name)
        result = self.command_runner.restart_container_immediately(name)
        if not result.success:
            WindowLog.log_error(result.error_message)

    # Delete operations
    def delete_entity(self):
        item = self.window.get_selected_item()
        if not item:
            return
        
        dialog = DeleteConfirmationDialog(self.window, item.getName())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._execute_background_task(self.__delete_entity_background_task, item)

    def __delete_entity_background_task(self, item):
        name = item.getName()
        type_str = "template" if item.type == Entity.TEMPLATE else "capsule"
        WindowLog.log_info(f"Deleting {type_str}: {name}...")

        success = False
        if item.type == Entity.CAPSULE:
            result = self.command_runner.delete_capsule(name)
            if not result.success:
                WindowLog.log_error(CallbackResult.FAILED_DELETE_CAPSULE.value)
                WindowLog.log_error(result.error_message)
                return
        else:
            result = self.command_runner.delete_template(name)
            if not result.success:
                WindowLog.log_error(CallbackResult.FAILED_DELETE_TEMPLATE.value)
                WindowLog.log_error(result.error_message)
                return
        
        WindowLog.log_info(CallbackResult.SUCCESS.value)

    # Utility operations
    def open_terminal(self):
        item = self.window.get_selected_item()
        if not item:
            return
        result = self.command_runner.open_terminal(item.getName())
        if not result.success:
            WindowLog.log_error(result.error_message)

    
    def open_shared_directory(self):
        item = self.window.get_selected_item()
        if not item:
            return
        result = self.command_runner.open_shared_directory(item.type, item.getName())
        if not result.success:
            WindowLog.log_error(result.error_message)

    def execute_command(self):
        item = self.window.get_selected_item()
        if not item or item.type != Entity.CAPSULE or item.getStatus() != ContainerStatus.RUNNING:
            return
        
        dialog = ExecuteCommandDialog(self.window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            command = dialog.get_command()
            if command:
                WindowLog.log_info(f"Executing command '{command}' in capsule '{item.getName()}'")
                result = self.command_runner.podman_command("exec -it", item.getName(), command, wait_for_finish=False)
                if not result.success:
                    WindowLog.log_error(result.error_message)


    # Xpra operations
    def attach_xpra(self):
        item = self.window.get_selected_item()
        if not item or item.type != Entity.CAPSULE:
            return
        
        capsule_name = item.getName()
        WindowLog.log_info(f"Attach Xpra to: {capsule_name}...")
        self._execute_background_task(self.__attach_xpra_background_task, capsule_name)

    def __attach_xpra_background_task(self, capsule_name: str):
        if not self.command_runner.xpra_is_attached(capsule_name):
            result = self.command_runner.xpra_attach(capsule_name)
            if not result.success:
                WindowLog.log_error(result.error_message)
            else:
                WindowLog.log_info(CallbackResult.SUCCESS.value)

    def detach_xpra(self):
        item = self.window.get_selected_item()
        if not item or item.type != Entity.CAPSULE:
            return
    
        capsule_name = item.getName()
        WindowLog.log_info(f"Detach Xpra from: {capsule_name}...")
        self._execute_background_task(self.__detach_xpra_background_task, capsule_name)

    def __detach_xpra_background_task(self, capsule_name: str):
        if self.command_runner.xpra_is_attached(capsule_name):
            result = self.command_runner.xpra_detach(capsule_name)
            if not result.success:
                WindowLog.log_error(result.error_message)
            else:
                WindowLog.log_info(CallbackResult.SUCCESS.value)
