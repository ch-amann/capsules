#! /usr/bin/env python3
#
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

import sys
from pathlib import Path
import argparse
from typing import List

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from window_log import WindowLog, WindowLogLevel
from settings import Settings
from command_runner import CommandRunner

def validate_ports(ports: List[str]) -> bool:
    """Check if ports are in format host:container[/protovol]. Host port cannot be below 1024. protocol must be tcp or udp"""
    for port_str in ports:
        parts = port_str.split(':')
        if len(parts) != 2:
            return False
        host_port, container_port = parts
        if '/' in container_port:
            container_port, protocol = container_port.split('/')
            if int(container_port) > 65535:
                return False
            if protocol not in ['tcp', 'udp']:
                return False
        else:
            protocol = 'tcp'
        try:
            host_port = int(host_port)
            if host_port < 1024 or host_port > 65535:
                return False
        except ValueError:
            return False
    return True

def log_handler(color: str, message: str) -> None:
    print(message)

def handle_container_operation(command_runner, operation: str, container_type: str, 
                             container_name: str) -> int:
    """Handle common container operations like start/stop/restart"""
    operation_map = {
        'start': command_runner.start_container,
        'stop': command_runner.stop_container_immediately,
        'restart': command_runner.restart_container_immediately
    }
    
    result = operation_map[operation](container_name)
    if not result.success:
        print(f"Failed to {operation} {container_type} {container_name}:")
        print(result.error_message)
        return 1
    return 0

def handle_execute_command(command_runner, container_name: str, cmd: List[str]) -> int:
    """Handle command execution in containers"""
    command = ' '.join(cmd)
    result = command_runner.podman_command("exec -it", container_name, command, 
                                         wait_for_finish=False)
    if not result.success:
        print("Failed to execute command:")
        print(result.error_message)
        return 1
    return 0

def print_entity_list(entities: List, headers: List[str], 
                     get_row_data: callable, filter_name: str = None) -> int:
    """Print formatted list of entities with optional name filter"""
    if filter_name:
        entities = [e for e in entities if e.name == filter_name]
        if not entities:
            print(f"No entity found with name: {filter_name}")
            return 1
    
    # Convert all values to strings and pad each column
    print("  ".join(f"{h:<20}" for h in headers))
    for entity in entities:
        row_data = [str(value) for value in get_row_data(entity)]
        print("  ".join(f"{val:<20}" for val in row_data))
    return 0

def validate_entity_name(command_runner, name: str, existing_names: List[str], 
                        entity_type: str) -> bool:
    """Validate entity name and show appropriate error messages"""
    if not command_runner.validate_name(name, existing_names, entity_type):
        return False
    return True

def handle_delete(command_runner, entity_name: str, existing_entities: List, delete_func: callable, entity_type: str) -> int:
    """Handle delete operation for templates and capsules"""
    existing_entity_names = [e.name for e in existing_entities]
    if entity_name not in existing_entity_names:
        print(f"{entity_type.capitalize()} '{entity_name}' not found. Available {entity_type}s: {', '.join(existing_entity_names)}")
        return 1
    result = delete_func(entity_name)
    if not result.success:
        print(f"Failed to delete {entity_type} {entity_name}:")
        print(result.error_message)
        return 1
    return 0

def handle_capsule_add(command_runner, args) -> bool:
    """Handle add operation for capsules"""
    existing_capsules = [c.name for c in command_runner.get_existing_capsules()]
    existing_templates = [t.name for t in command_runner.get_existing_templates()]
    
    if not validate_entity_name(command_runner, args.capsule_name, existing_capsules, "Capsule"):
        return False
    if args.capsule_name in existing_templates:
        print(f"Capsule name '{args.capsule_name}' is already in use by a template.")
        return False
    if args.template_name not in existing_templates:
        print(f"Template '{args.template_name}' not found. Available templates: {', '.join(existing_templates)}")
        return False
    if not validate_ports(args.ports):
        print(f"Invalid port mappings: {args.ports}. Port format: <1024-65535>:<1-65535>[/{{tcp/udp}}]")
        return False
    result = command_runner.create_capsule(
        args.capsule_name,
        args.template_name,
        not args.network_disabled,
        args.ports
    )
    if not result.success:
        print(f"Failed to create capsule {args.template_name}:")
        print(result.error_message)
        return False
    return True

def main():
    WindowLog.init(log_handler, WindowLogLevel.INFO)

    parser = argparse.ArgumentParser(
        description='Capsules CLI'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Base image commands
    baseimage_parser = subparsers.add_parser('baseimage', help='Base image operations')
    baseimage_subparsers = baseimage_parser.add_subparsers(dest='subcommand')
    
    baseimage_list = baseimage_subparsers.add_parser('list', help='List base images')
    baseimage_list.add_argument('--name', help='Filter by name')

    # Template commands
    template_parser = subparsers.add_parser('template', help='Template operations')
    template_subparsers = template_parser.add_subparsers(dest='subcommand')
    
    template_list = template_subparsers.add_parser('list', help='List templates')
    template_list.add_argument('--name', help='Filter by name')
    
    template_start = template_subparsers.add_parser('start', help='Start template')
    template_start.add_argument('template_name', help='Name of template to start')
    
    template_stop = template_subparsers.add_parser('stop', help='Stop template')
    template_stop.add_argument('template_name', help='Name of template to stop')
    
    template_restart = template_subparsers.add_parser('restart', help='Restart template')
    template_restart.add_argument('template_name', help='Name of template to restart')
    
    template_execute = template_subparsers.add_parser('execute', help='Execute command')
    template_execute.add_argument('template_name', help='Name of template to execute in')
    template_execute.add_argument('cmd', nargs='+', help='Command to execute')
    
    template_add = template_subparsers.add_parser('add', help='Add new template')
    template_add.add_argument('template_name', help='Name for new template')
    template_add.add_argument('baseimage', help='Base image to use')
    template_add.add_argument('--network_disabled', action='store_true',
                            help='Disable network access')
    
    template_del = template_subparsers.add_parser('delete', help='Delete template')
    template_del.add_argument('template_name', help='Name of template to delete')
    
    # Capsule commands
    capsule_parser = subparsers.add_parser('capsule', help='Capsule operations')
    capsule_subparsers = capsule_parser.add_subparsers(dest='subcommand')
    
    capsule_list = capsule_subparsers.add_parser('list', help='List capsules')
    capsule_list.add_argument('--name', help='Filter by name')
    
    capsule_start = capsule_subparsers.add_parser('start', help='Start capsule')
    capsule_start.add_argument('capsule_name', help='Name of capsule to start')
    
    capsule_stop = capsule_subparsers.add_parser('stop', help='Stop capsule')
    capsule_stop.add_argument('capsule_name', help='Name of capsule to stop')
    
    capsule_restart = capsule_subparsers.add_parser('restart', help='Restart capsule')
    capsule_restart.add_argument('capsule_name', help='Name of capsule to restart')
    
    capsule_execute = capsule_subparsers.add_parser('execute', help='Execute command')
    capsule_execute.add_argument('capsule_name', help='Name of capsule to execute in')
    capsule_execute.add_argument('cmd', nargs='+', help='Command to execute')

    capsule_add = capsule_subparsers.add_parser('add', help='Add new capsule')
    capsule_add.add_argument('capsule_name', help='Name for new capsule')
    capsule_add.add_argument('template_name', help='Template to use')
    capsule_add.add_argument('ports', nargs='*', help='Port mappings (host:container/protocol)')
    capsule_add.add_argument('--network_disabled', action='store_true',
                            help='Disable network access')
    
    capsule_del = capsule_subparsers.add_parser('delete', help='Delete capsule')
    capsule_del.add_argument('capsule_name', help='Name of capsule to delete')
    
    # Xpra commands as separate commands
    capsule_xpra_attach = capsule_subparsers.add_parser('xpra-attach', help='Attach xpra to capsule')
    capsule_xpra_attach.add_argument('capsule_name', help='Name of capsule')
    
    capsule_xpra_detach = capsule_subparsers.add_parser('xpra-detach', help='Detach xpra from capsule')
    capsule_xpra_detach.add_argument('capsule_name', help='Name of capsule')
    
    args = parser.parse_args()
    
    # Show help if no command or subcommand is given
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'baseimage' and not args.subcommand:
        baseimage_parser.print_help()
        return 1
    
    if args.command == 'template' and not args.subcommand:
        template_parser.print_help()
        return 1
    
    if args.command == 'capsule' and not args.subcommand:
        capsule_parser.print_help()
        return 1

    command_runner = CommandRunner(Settings())
    
    try:
        if args.command == 'baseimage':
            if args.subcommand == 'list':
                return print_entity_list(
                    command_runner.get_available_base_images(),
                    ["Name"],
                    lambda b: [b],
                    args.name
                )
                
        elif args.command == 'template':
            if args.subcommand == 'list':
                return print_entity_list(
                    command_runner.get_existing_templates(),
                    ["Name", "BaseImage", "Status", "Network"],
                    lambda t: [t.name, t.base_image, t.status.value, t.network],
                    args.name
                )
            if args.subcommand in ['start', 'stop', 'restart']:
                return handle_container_operation(command_runner, args.subcommand, 
                                               'template', args.template_name)
            elif args.subcommand == 'execute':
                return handle_execute_command(command_runner, args.template_name, args.cmd)
            elif args.subcommand == 'add':
                existing_base_images = command_runner.get_available_base_images()
                existing_templates = [t.name for t in command_runner.get_existing_templates()]
                existing_capsules = [c.name for c in command_runner.get_existing_capsules()]

                if args.template_name in existing_capsules:
                    print(f"Template name '{args.template_name}' is already in use by a capsule.")
                    return 1
                
                if not validate_entity_name(command_runner, args.template_name, 
                                          existing_templates, "Template"):
                    return 1
                    
                if args.baseimage not in existing_base_images:
                    print(f"Base image '{args.baseimage}' not found. "
                          f"Available base images: {', '.join(existing_base_images)}")
                    return 1
                    
                result = command_runner.create_template(
                    args.template_name,
                    args.baseimage,
                    not args.network_disabled
                )
                if not result.success:
                    print(f"Failed to create template {args.template_name}:")
                    print(result.error_message)
                    return 1
                
            elif args.subcommand == 'delete':
                return handle_delete(command_runner, args.template_name, 
                                  command_runner.get_existing_templates(), 
                                  command_runner.delete_template, 'template')

        elif args.command == 'capsule':
            if args.subcommand == 'list':
                return print_entity_list(
                    command_runner.get_existing_capsules(),
                    ["Name", "Template", "Status", "Network", "Ports", "Xpra"],
                    lambda c: [c.name, c.template, c.status.value, c.network, 
                             c.ports, c.xpra_attached],
                    args.name
                )
            if args.subcommand in ['start', 'stop', 'restart']:
                return handle_container_operation(command_runner, args.subcommand, 
                                               'capsule', args.capsule_name)
            elif args.subcommand == 'execute':
                return handle_execute_command(command_runner, args.capsule_name, args.cmd)
            elif args.subcommand == 'add':
                if not handle_capsule_add(command_runner, args):
                    return 1
            elif args.subcommand == 'delete':
                return handle_delete(command_runner, args.capsule_name, 
                                  command_runner.get_existing_capsules(), 
                                  command_runner.delete_capsule, 'capsule')
            elif args.subcommand in ['xpra-attach', 'xpra-detach']:
                operation = command_runner.xpra_attach if args.subcommand == 'xpra-attach' \
                          else command_runner.xpra_detach
                action = 'attach' if args.subcommand == 'xpra-attach' else 'detach'
                
                result = operation(args.capsule_name)
                if not result.success:
                    print(f"Failed to {action} xpra to capsule {args.capsule_name}:")
                    print(result.error_message)
                    return 1

        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

