"""Utility functions for quads-client"""


def extract_host_field(host, field_name, field_aliases=None, default=""):
    """
    Extract a field from a host that could be a string, dict, or object.

    Args:
        host: The host data (string, dict, or object)
        field_name: Primary field name to extract
        field_aliases: List of alternative field names to try
        default: Default value if field not found

    Returns:
        The extracted field value or default
    """
    if field_aliases is None:
        field_aliases = []

    # If host is a plain string and we're asking for 'name', return it
    # But only if it's not empty
    if isinstance(host, str):
        if field_name in ("name", "hostname"):
            return host if host else default
        else:
            return default

    # If host is a dict, try to get the field
    if isinstance(host, dict):
        if field_name in host:
            value = host[field_name]
            # Return value even if False (for booleans), but not if empty string
            if value is False or value:
                return value
        # Try aliases
        for alias in field_aliases:
            if alias in host:
                value = host[alias]
                if value is False or value:
                    return value
        return default

    # If host is an object, try attribute access
    if hasattr(host, field_name):
        value = getattr(host, field_name)
        # Return value even if False (for booleans), but not if empty string
        if value is False or value:
            return value
    # Try aliases
    for alias in field_aliases:
        if hasattr(host, alias):
            value = getattr(host, alias)
            if value is False or value:
                return value

    return default


def extract_hostname(host):
    """
    Extract hostname from a host that could be a string, dict, or object.

    Args:
        host: The host data (string, dict, or object)

    Returns:
        The hostname string or empty string if not found
    """
    return extract_host_field(host, "name", field_aliases=["hostname"], default="")


def get_ssl_indicator(url: str, verify: bool) -> tuple[str, str]:
    """
    Get SSL security indicator symbol and ANSI color for prompt display.

    Args:
        url: Server URL (http:// or https://)
        verify: Whether SSL verification is enabled

    Returns:
        tuple: (symbol, ansi_color_code)
            - ✓ (green) for HTTPS with verification
            - ! (green) for HTTPS without verification
            - ✗ (yellow) for HTTP
    """
    if url.startswith("https://"):
        if verify:
            return "✓", "\033[1;32m"
        else:
            return "!", "\033[1;32m"
    else:
        return "✗", "\033[1;33m"


def get_ssl_status_text(url: str, verify: bool) -> str:
    """
    Get SSL status text for table display.

    Args:
        url: Server URL (http:// or https://)
        verify: Whether SSL verification is enabled

    Returns:
        str: SSL status description
            - "HTTPS (verified)" for HTTPS with verification
            - "HTTPS (unverified)" for HTTPS without verification
            - "HTTP" for plain HTTP
    """
    if url.startswith("https://"):
        if verify:
            return "HTTPS (verified)"
        else:
            return "HTTPS (unverified)"
    else:
        return "HTTP"
