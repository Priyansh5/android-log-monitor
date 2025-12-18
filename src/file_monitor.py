import os
from pathlib import Path
from typing import List, Optional, Callable
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, QObject, pyqtSlot
from collections import deque

class FileMonitorWorker(QObject):
    """Worker class for file monitoring in background thread"""
    logs_ready = pyqtSignal(list)  # Emits list of new log lines
    error_occurred = pyqtSignal(str)  # Emits error message

    def __init__(self, log_file_path: str, max_batch_size: int = 10000):
        super().__init__()
        self.log_file_path = Path(log_file_path)
        self.max_batch_size = max_batch_size
        self.byte_offset = 0
        self.is_monitoring = False

    def start_monitoring(self):
        """Start monitoring the log file"""
        self.is_monitoring = True
        if self.log_file_path.exists():
            self.byte_offset = self.log_file_path.stat().st_size

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False

    @pyqtSlot()
    def check_for_new_logs(self):
        """Check for new log lines and emit signal if found"""
        if not self.is_monitoring or not self.log_file_path.exists():
            return

        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(self.byte_offset)
                new_lines = []
                while True:
                    line = f.readline()
                    if not line:
                        break
                    new_lines.append(line.rstrip('\n\r'))

                    # Prevent memory exhaustion
                    if len(new_lines) >= self.max_batch_size:
                        break

                if new_lines:
                    self.byte_offset = f.tell()
                    self.logs_ready.emit(new_lines)

        except (OSError, IOError) as e:
            self.error_occurred.emit(f"File monitoring error: {str(e)}")

class FileMonitor:
    """Main file monitor class with QTimer integration"""
    def __init__(self, config_manager, max_batch_size: int = 10000):
        self.config = config_manager
        self.max_batch_size = max_batch_size
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_timeout)

        self.worker = None
        self.thread = None
        self.log_file_path = None
        self.interval = self.config.get('timer_interval', 30) * 1000  # Convert to milliseconds

    def start_monitoring(self, log_file_path: str):
        """Start monitoring a log file"""
        self.log_file_path = log_file_path

        # Create worker in new thread
        self.thread = QThread()
        self.worker = FileMonitorWorker(log_file_path, self.max_batch_size)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.worker.logs_ready.connect(self._on_logs_ready)
        self.worker.error_occurred.connect(self._on_error)

        # Start thread and worker
        self.thread.started.connect(self.worker.start_monitoring)
        self.thread.start()

        # Start timer
        self.timer.start(self.interval)

    def stop_monitoring(self):
        """Stop monitoring"""
        self.timer.stop()

        if self.worker:
            self.worker.stop_monitoring()

        if self.thread:
            self.thread.quit()
            self.thread.wait(3000)  # Wait up to 3 seconds
            if self.thread.isRunning():
                self.thread.terminate()
            self.thread = None
            self.worker = None

    def _on_timer_timeout(self):
        """Called when timer fires - trigger log check in worker thread"""
        if self.worker and self.thread and self.thread.isRunning():
            # Use QMetaObject.invokeMethod for proper thread-safe call
            from PyQt6.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(self.worker, "check_for_new_logs", Qt.ConnectionType.QueuedConnection)

    def _on_logs_ready(self, lines: List[str]):
        """Handle new logs from worker"""
        # This will be overridden by GUI to handle the logs
        pass

    def _on_error(self, error_msg: str):
        """Handle errors from worker"""
        print(f"File monitor error: {error_msg}")

    def set_interval(self, seconds: int):
        """Update monitoring interval"""
        self.interval = seconds * 1000
        if self.timer.isActive():
            self.timer.setInterval(self.interval)

    def is_active(self) -> bool:
        """Check if monitoring is active"""
        return self.timer.isActive() and self.thread and self.thread.isRunning()
