from typing import Optional
import jwt

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
        self._user_role: Optional[str] = None
        self._registration_mode: bool = False

    @property
    def is_connected(self) -> bool:
        return self._current_server is not None and self._api is not None

    @property
    def is_authenticated(self) -> bool:
        """Check if user is logged in (has valid token)"""
        return self.is_connected and self._token is not None and not self._registration_mode

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

    @property
    def user_role(self) -> Optional[str]:
        """Get user role (admin or user)"""
        return self._user_role

    @property
    def is_admin(self) -> bool:
        """Check if current user has admin role"""
        return self._user_role == "admin"

    def _decode_role_from_token(self) -> Optional[str]:
        """Decode role from JWT token"""
        if not self._token:
            return None

        try:
            # Decode without verification (we already trust it from the server)
            decoded = jwt.decode(self._token, options={"verify_signature": False})
            # Check various possible role field names
            role = decoded.get("role") or decoded.get("roles") or decoded.get("user_role")
            if isinstance(role, list) and role:
                # If roles is a list, take the first one or look for 'admin'
                if "admin" in role:
                    return "admin"
                return role[0]
            return role
        except Exception:
            return None

    def connect(self, server_name: str, registration_mode: bool = False) -> None:
        """Connect to a server. If registration_mode=True, allows blank credentials."""
        if server_name not in self.config.get_all_servers():
            raise ConnectionError(f"Unknown server: {server_name}")

        url = self.config.get_server_url(server_name)
        username, password = self.config.get_server_credentials(server_name)
        verify = self.config.get_server_verify(server_name)

        # Allow blank credentials in registration mode
        if not registration_mode and (not username or not password):
            raise ConnectionError(
                f"Server '{server_name}' has no credentials. Use 'register' command to create an account."
            )

        try:
            if registration_mode or not username or not password:
                # Registration mode: connect without login
                api = QuadsApi(base_url=url, username="", password="", verify=verify)
                self._api = api
                self._current_server = server_name
                self._registration_mode = True
                self._username = None
                self._token = None
                self._user_role = None
            else:
                # Normal mode: connect and login
                api = QuadsApi(base_url=url, username=username, password=password, verify=verify)
                response = api.login()

                if response.get("status") != "success":
                    raise ConnectionError("Login failed")

                self._api = api
                self._token = api.token
                self._username = username
                self._current_server = server_name
                self._registration_mode = False

                # Try to decode role from token
                self._user_role = self._decode_role_from_token()

        except Exception as e:
            raise ConnectionError(f"Failed to connect to {server_name}: {e}")

    def disconnect(self) -> None:
        self._current_server = None
        self._api = None
        self._token = None
        self._username = None
        self._user_role = None
        self._registration_mode = False

    def get_available_servers(self) -> list[str]:
        return list(self.config.get_all_servers().keys())
