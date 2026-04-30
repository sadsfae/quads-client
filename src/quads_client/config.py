from pathlib import Path
from typing import Any, Optional

import yaml


class ConfigError(Exception):
    pass


class QuadsClientConfig:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = "~/.config/quads/quads-client.yml"
        self.config_path = Path(config_path).expanduser()
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            raise ConfigError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, "r") as f:
                self._config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ConfigError(f"Error reading config file: {e}")

        if "servers" not in self._config or not isinstance(self._config["servers"], dict):
            raise ConfigError("Config must contain 'servers' dictionary")

        if not self._config["servers"]:
            raise ConfigError("At least one server must be configured")

    def get_server(self, name: str) -> dict[str, Any]:
        servers = self._config.get("servers", {})
        if name not in servers:
            raise ConfigError(f"Server '{name}' not found in configuration")
        return servers[name]

    def get_all_servers(self) -> dict[str, dict[str, Any]]:
        return self._config.get("servers", {})

    def get_default_server(self) -> Optional[str]:
        return self._config.get("default_server")

    def get_server_url(self, name: str) -> str:
        server = self.get_server(name)
        if "url" not in server:
            raise ConfigError(f"Server '{name}' missing 'url' field")
        return server["url"]

    def get_server_credentials(self, name: str) -> tuple[str, str]:
        server = self.get_server(name)
        username = server.get("username", "")
        password = server.get("password", "")
        return username, password

    def get_server_verify(self, name: str) -> bool:
        server = self.get_server(name)
        verify = server.get("verify", True)
        if not isinstance(verify, bool):
            raise ConfigError(f"Server '{name}' verify must be true or false, not a path")
        return verify
