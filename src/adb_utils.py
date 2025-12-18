import subprocess
import platform
import re
from typing import List, Dict, Optional
from pathlib import Path

class DeviceInfo:
    def __init__(self, serial: str, status: str, model: str = ""):
        self.serial = serial
        self.status = status
        self.model = model

    def __str__(self):
        return f"{self.serial} ({self.status})"

class ADBUtils:
    def __init__(self):
        self.system = platform.system().lower()
        self.adb_path = self._find_adb()

    def _find_adb(self) -> Optional[str]:
        """Find ADB executable in system PATH"""
        try:
            result = subprocess.run(['adb', 'version'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return 'adb'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Check common installation paths
        common_paths = []
        if self.system == 'windows':
            common_paths = [
                r"C:\Program Files\Android\android-sdk\platform-tools\adb.exe",
                r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
                r"C:\Users\%USERNAME%\AppData\Local\Android\Sdk\platform-tools\adb.exe"
            ]
        elif self.system == 'linux':
            common_paths = [
                "/usr/bin/adb",
                "/usr/local/bin/adb",
                "~/Android/Sdk/platform-tools/adb"
            ]
        elif self.system == 'darwin':
            common_paths = [
                "/usr/local/bin/adb",
                "~/Library/Android/sdk/platform-tools/adb"
            ]

        for path_str in common_paths:
            path = Path(path_str).expanduser()
            if path.exists():
                return str(path)

        return None

    def is_adb_available(self) -> bool:
        """Check if ADB is available and working"""
        if not self.adb_path:
            return False

        try:
            result = subprocess.run([self.adb_path, 'version'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def get_connected_devices(self) -> List[DeviceInfo]:
        """Get list of connected Android devices"""
        if not self.adb_path:
            return []

        try:
            result = subprocess.run([self.adb_path, 'devices', '-l'],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return []

            devices = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip "List of devices attached"

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    status = parts[1]

                    # Extract model from device details
                    model = ""
                    if len(parts) > 2:
                        for part in parts[2:]:
                            if part.startswith('model:'):
                                model = part.split(':', 1)[1]
                                break

                    devices.append(DeviceInfo(serial, status, model))

            return devices
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return []

    def take_screenshot(self, serial: str, output_path: str) -> bool:
        """Take a screenshot and save it to the specified path"""
        if not self.adb_path:
            return False

        try:
            # Capture to device temp file
            temp_remote_path = "/sdcard/screen.png"
            subprocess.run([self.adb_path, '-s', serial, 'shell', 'screencap', '-p', temp_remote_path],
                         check=True, timeout=10)
            
            # Pull to local path
            subprocess.run([self.adb_path, '-s', serial, 'pull', temp_remote_path, output_path],
                         check=True, timeout=10)
            
            # Cleanup remote file
            subprocess.run([self.adb_path, '-s', serial, 'shell', 'rm', temp_remote_path],
                         timeout=5)
            
            return True
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"Screenshot failed: {e}")
            return False

    def clear_logcat(self, serial: Optional[str] = None) -> bool:
        """Clear logcat buffer"""
        if not self.adb_path:
            return False

        cmd = [self.adb_path, 'logcat', '-c']
        if serial:
            cmd = [self.adb_path, '-s', serial, 'logcat', '-c']

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def get_device_model(self, serial: str) -> str:
        """Get device model name"""
        if not self.adb_path:
            return "Unknown"

        try:
            result = subprocess.run([self.adb_path, '-s', serial, 'shell', 'getprop', 'ro.product.model'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

        return "Unknown"
    def test_device_connection(self, serial: str) -> bool:
        """Test connection to specific device"""
        if not self.adb_path:
            return False

        try:
            result = subprocess.run([self.adb_path, '-s', serial, 'shell', 'echo', 'test'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def clear_logcat(self, serial: str) -> bool:
        """Clear logcat buffer on device"""
        if not self.adb_path:
            return False

        try:
            result = subprocess.run([self.adb_path, '-s', serial, 'logcat', '-c'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def take_screenshot(self, serial: str, output_path: str) -> bool:
        """Take a screenshot from the device"""
        if not self.adb_path:
            return False

        try:
            # Take screenshot on device
            device_path = "/sdcard/screenshot_temp.png"
            result = subprocess.run([self.adb_path, '-s', serial, 'shell', 'screencap', '-p', device_path],
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return False

            # Pull screenshot to local machine
            result = subprocess.run([self.adb_path, '-s', serial, 'pull', device_path, output_path],
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return False

            # Clean up device screenshot
            subprocess.run([self.adb_path, '-s', serial, 'shell', 'rm', device_path],
                         capture_output=True, text=True, timeout=5)

            return True
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
