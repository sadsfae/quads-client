from typing import Optional

from quads_lib import QuadsApi

from quads_client.config import QuadsClientConfig


class ConnectionError(Exception):
    pass


class ConnectionManager:
    def __init__(self, config: QuadsClientConfig):
        self.config = config
        self._current_server: Optional[str] = None
        self._api: Optional[QuadsApi] = None
        self._token: Optional[str] = None
        self._username: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        return self._current_server is not None and self._api is not None

    @property
    def current_server(self) -> Optional[str]:
        return self._current_server

    @property
    def api(self) -> QuadsApi:
        if not self.is_connected or self._api is None:
            raise ConnectionError("Not connected to any server")
        return self._api

    @property
    def username(self) -> Optional[str]:
        return self._username

    def connect(self, server_name: str) -> None:
        if server_name not in self.config.get_all_servers():
            raise ConnectionError(f"Unknown server: {server_name}")

        url = self.config.get_server_url(server_name)
        username, password = self.config.get_server_credentials(server_name)

        if not username or not password:
            raise ConnectionError(f"Server '{server_name}' missing credentials")

        try:
            api = QuadsApi(url=url, username=username, password=password)
            response = api.login()

            if response.get("status") != "success":
                raise ConnectionError("Login failed")

            self._api = api
            self._token = api.token
            self._username = username
            self._current_server = server_name

        except Exception as e:
            raise ConnectionError(f"Failed to connect to {server_name}: {e}")

    def disconnect(self) -> None:
        self._current_server = None
        self._api = None
        self._token = None
        self._username = None

    def get_available_servers(self) -> list[str]:
        return list(self.config.get_all_servers().keys())
