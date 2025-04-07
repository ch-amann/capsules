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
Worker thread implementations for Capsules application.
Provides base worker and specialized workers for logging and command execution.
"""

from typing import Any, Callable, Optional, Tuple
from PyQt6.QtCore import (
    pyqtSignal, QObject, QWaitCondition, 
    QMutex, QThread, QMutexLocker
)

class BaseWorker(QObject):
    """Base class for worker threads with common functionality"""
    
    def __init__(self):
        """Initialize base worker with mutex and wait condition"""
        super().__init__()
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.worker_thread = QThread()
        self.moveToThread(self.worker_thread)
        self._running = True

    def start(self, signal: pyqtSignal, signal_handler: Callable, run_function: Callable) -> None:
        """Start the worker thread and connect signals"""
        signal.connect(signal_handler)
        self.worker_thread.started.connect(run_function)
        self.worker_thread.start()

    def stop(self) -> None:
        """Stop the worker thread gracefully"""
        with QMutexLocker(self.mutex):
            self._running = False
            self.wait_condition.wakeAll()
        self.worker_thread.quit()
        self.worker_thread.wait()


class LogWorker(BaseWorker):
    """Worker for handling log messages in a separate thread"""
    
    log_signal = pyqtSignal(str, str)  # color, message
    
    def __init__(self, log_signal_handler: Callable[[str, str], None]):
        """Initialize log worker"""
        super().__init__()
        self.color: Optional[str] = None
        self.message: Optional[str] = None
        self.start(self.log_signal, log_signal_handler, self.run)

    def run(self) -> None:
        """Main worker loop for processing log messages"""
        while self._running:
            with QMutexLocker(self.mutex):
                if self.message is None:
                    self.wait_condition.wait(self.mutex)
                if not self._running:
                    break
                if self.message and self.color:
                    log_color = self.color
                    log_message = self.message
                    self.color = None
                    self.message = None
                    self.log_signal.emit(log_color, log_message)

    def add_log(self, log_color: str, log_message: str) -> None:
        """Add a new log message to the queue"""
        with QMutexLocker(self.mutex):
            self.color = log_color
            self.message = log_message
            self.wait_condition.wakeOne()


class CommandWorker(BaseWorker):
    """Worker for executing commands in a separate thread"""
    
    command_done_signal = pyqtSignal()
    
    def __init__(self, command_done_signal_handler: Callable[[], None]):
        """Initialize command worker"""
        super().__init__()
        self.function: Optional[Callable] = None
        self.args: Optional[Tuple] = None
        self.kwargs: Optional[dict] = None
        self.start(self.command_done_signal, command_done_signal_handler, self.run)

    def run(self) -> None:
        """Main worker loop for executing commands"""
        while self._running:
            with QMutexLocker(self.mutex):
                if self.function is None:
                    self.wait_condition.wait(self.mutex)
                if not self._running:
                    break
                if self.function:
                    function = self.function
                    args = self.args or ()
                    kwargs = self.kwargs or {}
                    self.function = None
                    self.args = None
                    self.kwargs = None
                    try:
                        function(*args, **kwargs)
                    finally:
                        self.command_done_signal.emit()

    def execute_function(self, function: Callable, *args: Any, **kwargs: Any) -> None:
        """Queue a function for execution"""
        with QMutexLocker(self.mutex):
            self.function = function
            self.args = args
            self.kwargs = kwargs
            self.wait_condition.wakeOne()
