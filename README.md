# quads-client

[![pytest](https://github.com/redhat-performance/quads-client/actions/workflows/pytest.yml/badge.svg)](https://github.com/redhat-performance/quads-client/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/gh/redhat-performance/quads-client/branch/main/graph/badge.svg)](https://codecov.io/gh/redhat-performance/quads-client)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

QUADS Client is an interactive TUI (Text User Interface) shell for managing multiple QUADS server instances.

## Features

- **Multi-Server Support**: Connect to and manage multiple QUADS servers from a single interface
- **Bearer Token Authentication**: Secure JWT-based authentication via python-quads-lib
- **Interactive Shell**: Built on cmd2 with command history, tab completion, and help system
- **Self-Scheduling Mode (SSM)**: Non-admin users can schedule hosts for themselves
- **Command History**: SQLite-based persistent command history per server
- **Progress Tracking**: Real-time provisioning progress monitoring
- **Connection Management**: Easy switching between QUADS server instances
- **Thin Wrapper Design**: Server-side authorization via QUADS API

## Installation

### From RPM (Recommended)

```bash
dnf install quads-client
```

### From Source

```bash
git clone https://github.com/redhat-performance/quads-client.git
cd quads-client
python3 setup.py install
```

## Configuration

Create `~/.config/quads/quads-client.yml`:

```yaml
servers:
  quads1.rdu2.scalelab:
    url: https://quads1.rdu2.scalelab.example.com:5000
    username: admin@example.com
    password: your-password

  quads2.rdu2.scalelab:
    url: https://quads2.rdu2.scalelab.example.com:5000
    username: admin@example.com
    password: your-password

default_server: quads1.rdu2.scalelab
```

## Usage

### Interactive Mode

Launch the interactive shell:

```bash
quads-client
```

### One-Shot Commands

Execute a single command and exit:

```bash
quads-client connect quads1.rdu2.scalelab
quads-client cloud-list
```

## Commands

### Connection Management

```
connect [server]     - Connect to a QUADS server
disconnect           - Disconnect from current server
status               - Show connection status and user roles
```

### Cloud Management

```
cloud-list          - List all clouds
cloud-create <name> - Create a new cloud (admin only)
cloud-delete <name> - Delete a cloud (admin only)
```

### Self-Scheduling Mode (SSM)

```
ssm-available                - Show available hosts for self-scheduling
ssm-schedule <hostname> <cloud> - Schedule a host for yourself
ssm-my-hosts                 - Show your scheduled hosts
```

### Other Commands

```
version             - Show quads-client version
help [command]      - Show help for command(s)
exit / quit         - Exit the shell
```

## Authorization

quads-client is a thin wrapper around the QUADS API via python-quads-lib. All authorization is handled server-side by the QUADS server.

### Server Roles

The QUADS server implements two roles:

- **admin**: Full access to create/delete clouds, manage all schedules, and perform administrative operations
- **user**: Can view resources, create schedules, and use self-scheduling mode (SSM) on designated clouds

When a command requires elevated permissions, the server will return a 403 Forbidden error, which quads-client displays to the user.

### Self-Scheduling Mode (SSM)

SSM is a server-side feature (not a role) controlled by:
- Assignment flag: `is_self_schedule=True` on the cloud assignment
- Host flag: `can_self_schedule=True` on individual hosts

When scheduling on an SSM-enabled cloud, the server automatically calculates start/end dates based on configuration.

See [docs/INTEGRATION_ANALYSIS.md](docs/INTEGRATION_ANALYSIS.md) for complete API integration details.

## Architecture

```
quads-client/
├── src/quads_client/
│   ├── shell.py              - Main cmd2 shell
│   ├── config.py             - YAML configuration loader
│   ├── connection.py         - Multi-server connection manager
│   ├── auth.py               - Authorization exception class
│   ├── history.py            - SQLite command history
│   ├── progress.py           - Provisioning progress tracker
│   └── commands/             - Command modules
│       ├── connection.py     - Connection commands
│       ├── cloud.py          - Cloud management
│       ├── ssm.py            - Self-scheduling mode
│       └── version.py        - Version command
├── conf/
│   └── quads-client.yml.example - Example configuration
├── tests/                    - pytest test suite
└── docs/
    ├── INTEGRATION_ANALYSIS.md      - API integration details
    ├── QUADS_CLIENT_RBAC_AUDIT.md   - RBAC audit report
    ├── EXISTING_RBAC_ANALYSIS.md    - QUADS server RBAC analysis
    └── THIN_WRAPPER_CHANGES.md      - Thin wrapper implementation
```

## Dependencies

- Python >= 3.11
- cmd2 >= 2.0.0
- quads-lib >= 0.1.9
- PyYAML >= 6.0.0
- argcomplete >= 3.1.2
- tabulate >= 0.9.0

## Development

### Building from Source

```bash
python3 setup.py sdist
```

### Building RPM

```bash
rpmbuild -bb rpm/quads-client.spec \
  --define "_sourcedir $(pwd)/dist" \
  --define "_builddir $(pwd)/build" \
  --define "_rpmdir $(pwd)/rpms"
```

### Code Formatting

```bash
black --line-length 119 src/quads_client/
```

## Testing

### Run Tests

```bash
pytest tests/ -v
```

### Run Tests with Coverage

```bash
pytest tests/ --cov=quads_client --cov-report=html --cov-report=term
```

### Manual Testing

```bash
PYTHONPATH=src python3 -c "from quads_client.shell import QuadsClientShell; shell = QuadsClientShell()"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following DRY principles
4. Format code with black (line-length 119)
5. Test thoroughly
6. Submit a pull request

## License

GPLv3

## Links

- QUADS Server: https://github.com/redhat-performance/quads
- Documentation: https://quads.dev
- Issues: https://github.com/redhat-performance/quads-client/issues
