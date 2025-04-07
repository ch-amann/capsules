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

import signal
import sys
import fcntl
import atexit
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer

from main_window import MainWindow, ShowWindowEvent
from window_log import WindowLog

LOCK_FILE = "/tmp/capsules.lock"
APP_NAME = "Capsules"

class Application:
    def __init__(self):
        self.app: Optional[QApplication] = None
        self.window: Optional[MainWindow] = None
        self.lock_file = None
        self.icon: Optional[QIcon] = None

    def setup_single_instance(self) -> bool:
        """Try to obtain lock file and handle single instance"""
        # Check if lock file exists but is stale
        if Path(LOCK_FILE).exists():
            try:
                with open(LOCK_FILE, 'r') as f:
                    content = f.read().strip()
                    if content:  # File has content
                        pid = int(content)
                        try:
                            os.kill(pid, 0)  # Check if process exists
                            # Process exists, signal it
                            print("Other instance is running, sending signal to unhide it...")
                            os.kill(pid, signal.SIGUSR1)
                            return False
                        except ProcessLookupError:
                            # Process doesn't exist, remove stale lock
                            print("Removing stale lock file")
                            Path(LOCK_FILE).unlink()
                    else:  # Empty file
                        print("Removing empty lock file")
                        Path(LOCK_FILE).unlink()
            except (ValueError, OSError) as e:
                print(f"Lock file invalid, removing: {e}")
                Path(LOCK_FILE).unlink()

        # Create new lock file
        try:
            self.lock_file = open(LOCK_FILE, 'w')
            fcntl.lockf(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write PID to file
            pid = str(os.getpid())
            self.lock_file.write(pid)
            self.lock_file.flush()
            os.fsync(self.lock_file.fileno())
            print(f"Created lock file {LOCK_FILE} with PID {pid}")
            return True
            
        except IOError as e:
            print(f"Failed to create lock file: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up resources on application exit"""
        try:
            if hasattr(self, 'timer'):
                self.timer.stop()  # Stop timer before cleanup
            if self.lock_file:
                self.lock_file.close()
                Path(LOCK_FILE).unlink()
        except Exception as e:
            print(f"Cleanup error: {e}")

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for shutdown and window activation"""
        def sigint_handler(signum, frame):
            print("\nSIGINT received. Exiting...")
            if self.app:
                self.app.quit()

        def sigusr1_handler(signum, frame):
            # Schedule window activation through Qt's event loop
            if self.window:
                self.app.postEvent(self.window, ShowWindowEvent())

        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGUSR1, sigusr1_handler)

    def load_icon(self) -> None:
        """Load the application icon"""
        icon_path = Path(__file__).parent.parent / "res" / "icon_background.png"
        if not icon_path.exists():
            WindowLog.log_error(f"Icon not found at {icon_path}")
            return
        self.icon = QIcon(str(icon_path))

    def setup_ctrl_c_handler(self) -> None:
        """Setup timer to allow CTRL+C to interrupt Qt event loop"""
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: None)
        self.timer.start(500)

    def run(self) -> int:
        """Run the application"""
        # Prevent running as root
        if os.geteuid() == 0:
            print("This application should not be run as root")
            return 1

        # Create Qt application first
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(APP_NAME)

        # Check for single instance
        if not self.setup_single_instance():
            return 0  # Exit gracefully if another instance exists

        # Register cleanup and setup handlers
        atexit.register(self.cleanup)
        self.setup_signal_handlers()

        # Load and set icon
        self.load_icon()
        if self.icon:
            self.app.setWindowIcon(self.icon)

        # Create and show main window
        self.window = MainWindow(self.app, self.icon)
        self.window.show()

        # Setup CTRL+C handler
        self.setup_ctrl_c_handler()

        # Start event loop
        return self.app.exec()

def main() -> int:
    """Application entry point"""
    return Application().run()

if __name__ == "__main__":
    sys.exit(main())