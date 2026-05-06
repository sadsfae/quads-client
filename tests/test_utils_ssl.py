"""Tests for SSL utility functions in utils.py"""

import pytest

from quads_client.utils import get_ssl_indicator, get_ssl_status_text


class TestGetSSLIndicator:
    """Test get_ssl_indicator function"""

    def test_https_with_verification(self):
        """Test HTTPS URL with verification enabled"""
        symbol, color = get_ssl_indicator("https://quads1.example.com", True)
        assert symbol == "✓"
        assert color == "\033[1;32m"  # Green

    def test_https_without_verification(self):
        """Test HTTPS URL with verification disabled (self-signed)"""
        symbol, color = get_ssl_indicator("https://quads-dev.example.com", False)
        assert symbol == "!"
        assert color == "\033[1;32m"  # Green (still encrypted)

    def test_http_insecure(self):
        """Test HTTP URL (insecure, no encryption)"""
        symbol, color = get_ssl_indicator("http://quads-test.local", True)
        assert symbol == "✗"
        assert color == "\033[1;33m"  # Yellow

    def test_http_verify_false(self):
        """Test HTTP URL with verify=False (doesn't matter for HTTP)"""
        symbol, color = get_ssl_indicator("http://quads-test.local", False)
        assert symbol == "✗"
        assert color == "\033[1;33m"  # Yellow


class TestGetSSLStatusText:
    """Test get_ssl_status_text function"""

    def test_https_verified(self):
        """Test HTTPS with verification returns correct text"""
        text = get_ssl_status_text("https://quads1.example.com", True)
        assert text == "HTTPS (verified)"

    def test_https_unverified(self):
        """Test HTTPS without verification returns correct text"""
        text = get_ssl_status_text("https://quads-dev.example.com", False)
        assert text == "HTTPS (unverified)"

    def test_http(self):
        """Test HTTP returns correct text"""
        text = get_ssl_status_text("http://quads-test.local", True)
        assert text == "HTTP"

    def test_http_verify_false(self):
        """Test HTTP with verify=False returns correct text"""
        text = get_ssl_status_text("http://quads-test.local", False)
        assert text == "HTTP"

    def test_https_url_with_path(self):
        """Test HTTPS URL with path"""
        text = get_ssl_status_text("https://quads1.example.com/api/v3", True)
        assert text == "HTTPS (verified)"

    def test_http_url_with_path(self):
        """Test HTTP URL with path"""
        text = get_ssl_status_text("http://quads-test.local:5000/api", False)
        assert text == "HTTP"
