import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

class FilterPresetManager(QObject):
    """Manages filter presets for saving and loading filter configurations"""
    presets_changed = pyqtSignal()
    
    def __init__(self, presets_dir="config/presets"):
        super().__init__()
        self.presets_dir = Path(presets_dir)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        self.last_preset_file = self.presets_dir.parent / "last_preset.txt"
        self.ensure_default_presets()

    def ensure_default_presets(self):
        """Create default presets if they don't exist"""
        defaults = {
            "Errors Only": {
                "levels": {"ERROR": True, "FATAL": True, "WARN": False, "INFO": False, "DEBUG": False, "VERBOSE": False},
                "tags": [], "keywords": [], "exclude_tags": [], "regex_enabled": False
            },
            "App Crashes": {
                "levels": {"ERROR": True, "FATAL": True, "WARN": False, "INFO": False, "DEBUG": False, "VERBOSE": False},
                "tags": ["AndroidRuntime"], "keywords": ["FATAL EXCEPTION", "Force finishing"], 
                "exclude_tags": [], "regex_enabled": False
            },
            "Network Debug": {
                "levels": {"ERROR": True, "FATAL": True, "WARN": True, "INFO": True, "DEBUG": True, "VERBOSE": True},
                "tags": ["OkHttp", "Retrofit", "Volley", "NetworkSecurityConfig"], 
                "keywords": [], "exclude_tags": [], "regex_enabled": False
            },
            "System GC": {
                "levels": {"ERROR": False, "FATAL": False, "WARN": False, "INFO": True, "DEBUG": True, "VERBOSE": True},
                "tags": ["dalvikvm", "art", "System.err"], 
                "keywords": ["GC_"], "exclude_tags": [], "regex_enabled": False
            }
        }

        for name, data in defaults.items():
            if not (self.presets_dir / f"{name}.json").exists():
                self.save_preset(name, data)
    
    def save_preset(self, name: str, preset_data: Dict[str, Any]) -> bool:
        """Save a filter preset"""
        try:
            preset_file = self.presets_dir / f"{name}.json"
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=2)
            self.presets_changed.emit()
            return True
        except Exception as e:
            print(f"Error saving preset: {e}")
            return False
    
    def load_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a filter preset"""
        try:
            preset_file = self.presets_dir / f"{name}.json"
            if preset_file.exists():
                with open(preset_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading preset: {e}")
        return None
    
    def delete_preset(self, name: str) -> bool:
        """Delete a filter preset"""
        try:
            preset_file = self.presets_dir / f"{name}.json"
            if preset_file.exists():
                preset_file.unlink()
                self.presets_changed.emit()
                return True
        except Exception as e:
            print(f"Error deleting preset: {e}")
        return False
    
    def list_presets(self) -> List[str]:
        """List all available presets"""
        try:
            presets = []
            for file in self.presets_dir.glob("*.json"):
                presets.append(file.stem)
            return sorted(presets)
        except Exception as e:
            print(f"Error listing presets: {e}")
            return []
    
    def save_last_preset(self, name: str):
        """Save the name of the last used preset"""
        try:
            with open(self.last_preset_file, 'w', encoding='utf-8') as f:
                f.write(name)
        except Exception as e:
            print(f"Error saving last preset: {e}")
    
    def get_last_preset(self) -> Optional[str]:
        """Get the name of the last used preset"""
        try:
            if self.last_preset_file.exists():
                with open(self.last_preset_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Error getting last preset: {e}")
        return None
