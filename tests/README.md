# quads-client Test Suite

## Overview

Comprehensive test suite for quads-client using pytest.

## Test Structure

```
tests/
├── conftest.py                 - Pytest fixtures and mocks
├── test_config.py              - Configuration loading tests
├── test_connection.py          - Connection manager tests
├── test_commands_cloud.py      - Cloud command tests
├── test_commands_ssm.py        - SSM command tests
└── test_commands_connection.py - Connection command tests
```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run with coverage
```bash
pytest tests/ --cov=quads_client --cov-report=html --cov-report=term
```

### Run specific test file
```bash
pytest tests/test_config.py -v
```

### Run specific test
```bash
pytest tests/test_config.py::test_config_load_valid_yaml -v
```

### Run tests by marker
```bash
pytest tests/ -m unit
```

## Test Categories

- **Unit tests**: Test individual functions/methods in isolation
- **Integration tests**: Test component interactions (marked with `@pytest.mark.integration`)
- **Slow tests**: Long-running tests (marked with `@pytest.mark.slow`)

## Coverage Goals

- Overall coverage: 80%+
- Critical paths (connection, auth): 90%+
- Command modules: 75%+

## Fixtures

### mock_config
Mock QuadsClientConfig with test server configuration

### mock_api
Mock QuadsApi with standard responses

### mock_connection_manager
Mock ConnectionManager with authenticated connection

### mock_shell
Mock QuadsClientShell for command testing

## Adding New Tests

1. Create test file: `test_<module>.py`
2. Import fixtures from conftest
3. Write test functions prefixed with `test_`
4. Use descriptive test names
5. Add docstrings explaining what is tested
6. Use markers for categorization

Example:
```python
import pytest
from quads_client.mymodule import MyClass

def test_myclass_success(mock_shell):
    """Test MyClass method succeeds with valid input"""
    obj = MyClass(mock_shell)
    result = obj.method("valid_input")
    assert result == expected_value
```

## Continuous Integration

Tests run automatically on:
- Push to main/latest/develop branches
- Pull requests to main/latest
- Coverage reports uploaded to Codecov

See `.github/workflows/pytest.yml` and `.github/workflows/codecov.yml`
