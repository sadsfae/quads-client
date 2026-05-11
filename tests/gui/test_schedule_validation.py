"""Tests for hostname validation in schedule views"""

import unittest
from unittest.mock import Mock


class TestScheduleValidation(unittest.TestCase):
    """Test hostname validation in SSM schedule view"""

    def setUp(self):
        """Set up test fixtures"""
        self.api = Mock()

    def _validate_hostnames(self, hostnames):
        """Extracted validation logic from ScheduleView for testing

        This is a copy of the validation method to allow testing without GUI dependencies
        """
        errors = []

        for hostname in hostnames:
            hostname = hostname.strip()
            if not hostname:
                continue

            try:
                host = self.api.get_host(hostname)

                if not host:
                    errors.append(f"{hostname}: Host not found (typo?)")
                    continue

                if host.get("broken"):
                    errors.append(f"{hostname}: Host is marked as broken")
                    continue

                if host.get("retired"):
                    errors.append(f"{hostname}: Host is retired")
                    continue

                if not host.get("can_self_schedule"):
                    errors.append(f"{hostname}: Not enabled for self-scheduling")
                    continue

            except Exception as e:
                errors.append(f"{hostname}: Error checking host ({str(e)})")

        return (len(errors) == 0, errors)

    def test_validate_hostnames_all_valid(self):
        """Test validation passes when all hostnames are valid"""

        def mock_get_host(hostname):
            return {"name": hostname, "broken": False, "retired": False, "can_self_schedule": True}

        self.api.get_host = mock_get_host

        hostnames = ["host01.example.com", "host02.example.com"]
        is_valid, errors = self._validate_hostnames(hostnames)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_hostnames_not_found(self):
        """Test validation fails for non-existent hostname"""
        self.api.get_host = Mock(return_value=None)

        hostnames = ["bogus-host.example.com"]
        is_valid, errors = self._validate_hostnames(hostnames)

        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIn("bogus-host.example.com", errors[0])
        self.assertIn("not found", errors[0].lower())

    def test_validate_hostnames_broken(self):
        """Test validation fails for broken host"""
        self.api.get_host = Mock(
            return_value={"name": "broken-host.example.com", "broken": True, "retired": False, "can_self_schedule": True}
        )

        hostnames = ["broken-host.example.com"]
        is_valid, errors = self._validate_hostnames(hostnames)

        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIn("broken-host.example.com", errors[0])
        self.assertIn("broken", errors[0].lower())

    def test_validate_hostnames_retired(self):
        """Test validation fails for retired host"""
        self.api.get_host = Mock(
            return_value={"name": "retired-host.example.com", "broken": False, "retired": True, "can_self_schedule": True}
        )

        hostnames = ["retired-host.example.com"]
        is_valid, errors = self._validate_hostnames(hostnames)

        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIn("retired-host.example.com", errors[0])
        self.assertIn("retired", errors[0].lower())

    def test_validate_hostnames_not_ssm_enabled(self):
        """Test validation fails for host not enabled for self-scheduling"""
        self.api.get_host = Mock(
            return_value={"name": "no-ssm.example.com", "broken": False, "retired": False, "can_self_schedule": False}
        )

        hostnames = ["no-ssm.example.com"]
        is_valid, errors = self._validate_hostnames(hostnames)

        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIn("no-ssm.example.com", errors[0])
        self.assertIn("self-scheduling", errors[0].lower())

    def test_validate_hostnames_mixed_valid_invalid(self):
        """Test validation with mix of valid and invalid hostnames"""

        def mock_get_host(hostname):
            if hostname == "valid-host.example.com":
                return {"name": hostname, "broken": False, "retired": False, "can_self_schedule": True}
            elif hostname == "broken-host.example.com":
                return {"name": hostname, "broken": True, "retired": False, "can_self_schedule": True}
            else:
                return None

        self.api.get_host = mock_get_host

        hostnames = ["valid-host.example.com", "broken-host.example.com", "missing-host.example.com"]
        is_valid, errors = self._validate_hostnames(hostnames)

        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 2)

    def test_validate_hostnames_empty_list(self):
        """Test validation with empty hostname list"""
        hostnames = []
        is_valid, errors = self._validate_hostnames(hostnames)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_hostnames_whitespace_only(self):
        """Test validation skips whitespace-only entries"""
        self.api.get_host = Mock(
            return_value={"name": "valid-host.example.com", "broken": False, "retired": False, "can_self_schedule": True}
        )

        hostnames = ["valid-host.example.com", "  ", "", "\t"]
        is_valid, errors = self._validate_hostnames(hostnames)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_hostnames_api_exception(self):
        """Test validation handles API exceptions gracefully"""
        self.api.get_host = Mock(side_effect=Exception("API error"))

        hostnames = ["error-host.example.com"]
        is_valid, errors = self._validate_hostnames(hostnames)

        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIn("error-host.example.com", errors[0])
        self.assertIn("Error checking", errors[0])


if __name__ == "__main__":
    unittest.main()
