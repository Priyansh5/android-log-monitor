import json
import os
from pathlib import Path

class ConfigManager:
    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "user_config.json"
        self.default_config_file = self.config_dir / "default_config.json"
        self.config = {}
        self.load_config()

    def load_config(self):
        """Load configuration from file, falling back to defaults"""
        try:
            # Load defaults first
            with open(self.default_config_file, 'r') as f:
                self.config = json.load(f)

            # Override with user config if exists
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    self._deep_update(self.config, user_config)
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = {}

    def save_config(self):
        """Save current configuration to user config file"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key, value):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()

    def _deep_update(self, base_dict, update_dict):
        """Recursively update dictionary"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
