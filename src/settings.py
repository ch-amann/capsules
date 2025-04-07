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
Settings management for Capsules application.
Handles configuration files for global settings, templates and capsules.
"""

from configparser import ConfigParser
from pathlib import Path
from dataclasses import dataclass

from misc import UserAppDir
from utils import get_capsule_dir, get_template_dir
from window_log import WindowLog

@dataclass
class ConfigPaths:
    """Paths for configuration and metadata files"""
    SETTINGS_FILE: str = "settings.ini"
    METADATA_FILE: str = ".metadata"

class Settings:
    """Manages application settings and configuration files"""
    
    def __init__(self):
        """Initialize settings and create default global config if needed"""
        self.config_paths = ConfigPaths()
        self._ensure_global_config()

    def _ensure_global_config(self) -> None:
        """Create default global config if it doesn't exist"""
        config_path = self._get_path(UserAppDir, self.config_paths.SETTINGS_FILE)
        if not config_path.exists():
            config = self.generate_global_default_config()
            self._store_config(config_path, config)

    def _get_path(self, base_dir: Path, filename: str) -> Path:
        """Get full path for a config file"""
        return base_dir / filename

    def _read_config(self, file_path: Path) -> ConfigParser:
        """Read and parse a config file, creating default if needed"""
        config = ConfigParser()
        try:
            if file_path.exists():
                config.read(file_path)
            else:
                WindowLog.log_debug(f"Config file not found, using defaults: {file_path}")
        except Exception as e:
            WindowLog.log_error(f"Error reading config {file_path}: {e}")
        return config

    def _store_config(self, file_path: Path, config: ConfigParser) -> bool:
        """Store config to file with error handling"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as configfile:
                config.write(configfile)
            return True
        except Exception as e:
            WindowLog.log_error(f"Error writing config {file_path}: {e}")
            return False

    # Global config methods
    def get_global_config(self) -> ConfigParser:
        """Get global configuration"""
        return self._read_config(self._get_path(UserAppDir, self.config_paths.SETTINGS_FILE))

    def store_global_config(self, config: ConfigParser) -> bool:
        """Store global configuration"""
        return self._store_config(
            self._get_path(UserAppDir, self.config_paths.SETTINGS_FILE), 
            config
        )

    # Template config methods
    def get_template_config(self, template_name: str) -> ConfigParser:
        """Get template-specific configuration"""
        return self._read_config(
            self._get_path(get_template_dir(template_name), self.config_paths.SETTINGS_FILE)
        )

    def store_template_config(self, template_name: str, config: ConfigParser) -> bool:
        """Store template-specific configuration"""
        return self._store_config(
            self._get_path(get_template_dir(template_name), self.config_paths.SETTINGS_FILE),
            config
        )

    # Capsule config methods
    def get_capsule_config(self, capsule_name: str) -> ConfigParser:
        """Get capsule-specific configuration"""
        return self._read_config(
            self._get_path(get_capsule_dir(capsule_name), self.config_paths.SETTINGS_FILE)
        )

    def store_capsule_config(self, capsule_name: str, config: ConfigParser) -> bool:
        """Store capsule-specific configuration"""
        return self._store_config(
            self._get_path(get_capsule_dir(capsule_name), self.config_paths.SETTINGS_FILE),
            config
        )

    def get_capsule_metadata(self, capsule_name: str) -> ConfigParser:
        """Get capsule metadata"""
        return self._read_config(
            self._get_path(get_capsule_dir(capsule_name), self.config_paths.METADATA_FILE)
        )

    def store_capsule_metadata(self, capsule_name: str, metadata: ConfigParser) -> bool:
        """Store capsule metadata"""
        return self._store_config(
            self._get_path(get_capsule_dir(capsule_name), self.config_paths.METADATA_FILE),
            metadata
        )

    # Configuration generators
    @staticmethod
    def generate_global_default_config() -> ConfigParser:
        """Generate default global configuration"""
        config = ConfigParser()
        config['DEFAULT'] = {'terminal': ''}
        return config

    @staticmethod
    def generate_capsule_metadata(network: str) -> ConfigParser:
        """Generate default capsule metadata"""
        config = ConfigParser()
        config['Network'] = {'network': network}
        return config
