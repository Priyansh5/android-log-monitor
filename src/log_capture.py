import subprocess
import platform
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import threading

class LogCapture:
    def __init__(self, adb_utils, logs_dir="logs"):
        self.adb_utils = adb_utils
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        self.system = platform.system().lower()
        self.process: Optional[subprocess.Popen] = None
        self.log_file: Optional[Path] = None
        self.device_serial: Optional[str] = None

    def start_capture(self, device_serial: str) -> bool:
        """Start log capture for specified device"""
        if not self.adb_utils.is_adb_available():
            raise Exception("ADB is not available")

        if not self.adb_utils.test_device_connection(device_serial):
            raise Exception(f"Cannot connect to device {device_serial}")

        self.device_serial = device_serial

        # Clear existing logcat buffer
        self.adb_utils.clear_logcat(device_serial)

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = self.logs_dir / f"android_logs_{timestamp}.txt"

        # Start capture process
        success = self._launch_terminal_process(device_serial)
        if success:
            print(f"Log capture started. Logs saved to: {self.log_file}")
        return success

    def stop_capture(self) -> bool:
        """Stop log capture"""
        if self.process:
            try:
                # Terminate the process tree
                if self.system == 'windows':
                    subprocess.run(['taskkill', '/T', '/F', '/PID', str(self.process.pid)],
                                 capture_output=True)
                else:
                    os.killpg(os.getpgid(self.process.pid), 15)  # SIGTERM

                self.process.wait(timeout=5)
                self.process = None
                print("Log capture stopped")
                return True
            except (subprocess.TimeoutExpired, OSError, ProcessLookupError):
                try:
                    if self.system == 'windows':
                        self.process.kill()
                    else:
                        os.killpg(os.getpgid(self.process.pid), 9)  # SIGKILL
                    self.process = None
                    return True
                except Exception:
                    return False
        return False

    def _launch_terminal_process(self, device_serial: str) -> bool:
        """Launch platform-specific terminal with ADB logcat"""
        try:
            if self.system == 'windows':
                # For Windows, run ADB directly and redirect to file
                adb_cmd = f"{self.adb_utils.adb_path} -s {device_serial} logcat -v threadtime"
                # Run ADB directly and redirect output to file
                self.process = subprocess.Popen(
                    adb_cmd,
                    shell=True,
                    stdout=open(self.log_file, 'w'),
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # Linux/macOS
                cmd = self._build_command(device_serial)
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid  # Create new process group
                )
            return True
        except Exception as e:
            print(f"Failed to launch terminal process: {e}")
            return False

    def _build_command(self, device_serial: str) -> list:
        """Build platform-specific command for ADB logcat with tee"""
        adb_cmd = f"{self.adb_utils.adb_path} -s {device_serial} logcat -v threadtime"

        if self.system == 'windows':
            # Windows: Use PowerShell tee equivalent or fallback to direct redirection
            # PowerShell has Tee-Object, but for simplicity, use direct redirection
            # since subprocess handles stdout redirection
            return [adb_cmd, '>', str(self.log_file)]

        elif self.system == 'linux':
            # Linux: Use gnome-terminal, xterm, or konsole
            terminals = ['gnome-terminal', 'xterm', 'konsole']
            terminal_cmd = None

            for term in terminals:
                if self._is_command_available(term):
                    if term == 'gnome-terminal':
                        terminal_cmd = [
                            'gnome-terminal', '--', 'bash', '-c',
                            f'{adb_cmd} | tee "{self.log_file}"; exec bash'
                        ]
                    elif term == 'konsole':
                        terminal_cmd = [
                            'konsole', '-e', 'bash', '-c',
                            f'{adb_cmd} | tee "{self.log_file}"; exec bash'
                        ]
                    elif term == 'xterm':
                        terminal_cmd = [
                            'xterm', '-e', 'bash', '-c',
                            f'{adb_cmd} | tee "{self.log_file}"; exec bash'
                        ]
                    break

            if terminal_cmd:
                return terminal_cmd
            else:
                # Fallback to direct execution (no visible terminal)
                return ['bash', '-c', f'{adb_cmd} > "{self.log_file}"']

        elif self.system == 'darwin':
            # macOS: Use Terminal.app or iTerm2
            if self._is_command_available('iterm2'):
                return [
                    'osascript', '-e',
                    f'tell application "iTerm2" to create window with default profile command "{adb_cmd} | tee \\"{self.log_file}\\""'
                ]
            else:
                return [
                    'osascript', '-e',
                    f'tell application "Terminal" to do script "{adb_cmd} | tee \\"{self.log_file}\\""'
                ]

        # Fallback
        return [adb_cmd, '>', str(self.log_file)]

    def _is_command_available(self, command: str) -> bool:
        """Check if command is available in PATH"""
        try:
            subprocess.run([command, '--version'], capture_output=True, timeout=2)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False

    def is_capturing(self) -> bool:
        """Check if capture is currently running"""
        if not self.process:
            return False

        return self.process.poll() is None

    def get_log_file_path(self) -> Optional[str]:
        """Get current log file path"""
        return str(self.log_file) if self.log_file else None
