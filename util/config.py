"""
version: 0.1.0
author: Wuyilingwei
Config file loader
"""
import os
import logging
from typing import Any, Dict, Optional
import toml


class Config:
    """
    Config class to load and save config file
    """
    config_path: str
    config: Dict[str, Any]
    logger: logging.Logger

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Load config file from config_path
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")
        self.config_path = config_path
        self.config = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.load_config()

    def __getitem__(self, key: str) -> Any:
        """
        Allow dictionary-style access to the config
        """
        return self.config[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Allow dictionary-style setting of the config
        """
        self.config[key] = value

    def load_config(self) -> None:
        """
        Load config file from config_path
        """
        if not os.path.exists(self.config_path):
            self.logger.warning(f"Config file {self.config_path} not found")
            self.config = {}
        else:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = toml.load(f)
                self.logger.info(f"Config file loaded from {self.config_path}")
                self.logger.debug(f"Config file content: {self.config}")
        self.validate_config()

    def validate_config(self) -> None:
        """
        Validate config file
        """
        default_config = {
            "translator": {
                "type": "google",
                "api_key": None,
                "source_lang": "auto",
                "target_lang": "en",
            },
            "workshop": {
                "game_id": 0,
                "text": "Mod",
            },
        }

        def validate_recursive(current: Dict[str, Any], default: Dict[str, Any]) -> None:
            """
            Recursively validate and update the current config with default values
            """
            for key, value in default.items():
                if key not in current:
                    current[key] = value
                    self.logger.warning(f"Config file missing {key}, using default value {value}")
                elif isinstance(value, dict) and isinstance(current[key], dict):
                    validate_recursive(current[key], value)
        validate_recursive(self.config, default_config)

    def save_config(self) -> None:
        """
        Save config file to config_path
        """
        with open(self.config_path, "w", encoding="utf-8") as f:
            toml.dump(self.config, f)
        print(f"Config file saved to {self.config_path}")


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={'disable': ['E9999', 'E9998', 'W1203'], "max-line-length": 120})
    config = Config()
    config.save_config()
