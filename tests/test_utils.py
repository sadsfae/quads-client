import pytest
from quads_client.utils import extract_host_field, extract_hostname


def test_extract_hostname_from_string():
    """Test extracting hostname from plain string"""
    hostname = "host01.example.com"
    result = extract_hostname(hostname)
    assert result == "host01.example.com"


def test_extract_hostname_from_dict():
    """Test extracting hostname from dict with 'name' key"""
    host = {"name": "host01.example.com", "model": "r640"}
    result = extract_hostname(host)
    assert result == "host01.example.com"


def test_extract_hostname_from_dict_with_alias():
    """Test extracting hostname from dict with 'hostname' key"""
    host = {"hostname": "host01.example.com", "model": "r640"}
    result = extract_hostname(host)
    assert result == "host01.example.com"


def test_extract_hostname_from_object():
    """Test extracting hostname from object with name attribute"""

    class Host:
        def __init__(self):
            self.name = "host01.example.com"
            self.model = "r640"

    host = Host()
    result = extract_hostname(host)
    assert result == "host01.example.com"


def test_extract_hostname_from_object_with_alias():
    """Test extracting hostname from object with hostname attribute"""

    class Host:
        def __init__(self):
            self.hostname = "host01.example.com"
            self.model = "r640"

    host = Host()
    result = extract_hostname(host)
    assert result == "host01.example.com"


def test_extract_hostname_empty_dict():
    """Test extracting hostname from empty dict returns empty string"""
    host = {"model": "r640"}
    result = extract_hostname(host)
    assert result == ""


def test_extract_hostname_empty_object():
    """Test extracting hostname from object without name returns empty string"""

    class Host:
        def __init__(self):
            self.model = "r640"

    host = Host()
    result = extract_hostname(host)
    assert result == ""


def test_extract_host_field_string():
    """Test extract_host_field with string returns default for non-name fields"""
    hostname = "host01.example.com"
    result = extract_host_field(hostname, "model", default="N/A")
    assert result == "N/A"


def test_extract_host_field_from_dict():
    """Test extract_host_field from dict"""
    host = {"name": "host01.example.com", "model": "r640", "host_type": "baremetal"}
    assert extract_host_field(host, "model") == "r640"
    assert extract_host_field(host, "host_type") == "baremetal"


def test_extract_host_field_from_dict_with_alias():
    """Test extract_host_field from dict with alias"""
    host = {"host_model": "r640"}
    result = extract_host_field(host, "model", field_aliases=["host_model"])
    assert result == "r640"


def test_extract_host_field_from_object():
    """Test extract_host_field from object"""

    class Host:
        def __init__(self):
            self.name = "host01.example.com"
            self.model = "r640"
            self.host_type = "baremetal"

    host = Host()
    assert extract_host_field(host, "model") == "r640"
    assert extract_host_field(host, "host_type") == "baremetal"


def test_extract_host_field_from_object_with_alias():
    """Test extract_host_field from object with alias"""

    class Host:
        def __init__(self):
            self.host_model = "r640"

    host = Host()
    result = extract_host_field(host, "model", field_aliases=["host_model"])
    assert result == "r640"


def test_extract_host_field_default_value():
    """Test extract_host_field returns default when field not found"""
    host = {"name": "host01.example.com"}
    result = extract_host_field(host, "model", default="unknown")
    assert result == "unknown"


def test_extract_host_field_boolean():
    """Test extract_host_field with boolean values"""
    host = {"can_self_schedule": True}
    result = extract_host_field(host, "can_self_schedule", default=False)
    assert result is True

    host2 = {"can_self_schedule": False}
    result2 = extract_host_field(host2, "can_self_schedule", default=True)
    assert result2 is False


def test_extract_host_field_empty_string_for_name():
    """Test extract_host_field with empty string for name field"""
    result = extract_host_field("", "name", default="N/A")
    assert result == "N/A"


def test_extract_host_field_none_aliases():
    """Test extract_host_field with None aliases (default parameter)"""
    host = {"model": "r640"}
    result = extract_host_field(host, "model")
    assert result == "r640"
