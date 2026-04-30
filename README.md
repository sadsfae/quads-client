# quads-client

[![pytest](https://github.com/quadsproject/quads-client/actions/workflows/pytest.yml/badge.svg)](https://github.com/redhat-performance/quads-client/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/gh/quadsproject/quads-client/branch/main/graph/badge.svg)](https://codecov.io/gh/redhat-performance/quads-client)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

QUADS Client is an interactive TUI (Text User Interface) shell for managing multiple QUADS server instances.

## Features

- **Multi-Server Support**: Connect to and manage multiple QUADS servers from a single interface
- **Bearer Token Authentication**: Secure JWT-based authentication via python-quads-lib
- **Interactive Shell**: Built on cmd2 with command history, tab completion, and help system
- **User Registration**: Non-admin users can register accounts and manage their own assignments
- **Command History**: SQLite-based persistent command history per server
- **Progress Tracking**: Real-time provisioning progress monitoring
- **Connection Management**: Easy switching between QUADS server instances
- **Thin Wrapper Design**: Server-side authorization via QUADS API

## Table of Contents

- [Installation](#installation)
  - [From RPM (Recommended)](#from-rpm-recommended)
  - [From Source](#from-source)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Interactive Mode](#interactive-mode)
  - [One-Shot Commands](#one-shot-commands)
- [Commands](#commands)
  - [Connection Management](#connection-management)
  - [Server Management](#server-management)
  - [Cloud Management](#cloud-management)
  - [User & Assignment Commands](#user--assignment-commands)
  - [Host Management (Admin)](#host-management-admin)
  - [Schedule Management (Admin)](#schedule-management-admin)
  - [Available Hosts](#available-hosts)
  - [Other Commands](#other-commands)
- [Authorization](#authorization)
  - [Server Roles](#server-roles)
  - [User Registration & Assignments](#user-registration--assignments)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Development](#development)
  - [Building from Source](#building-from-source)
  - [Building RPM](#building-rpm)
  - [Code Formatting](#code-formatting)
- [Testing](#testing)
  - [Run Tests](#run-tests)
  - [Run Tests with Coverage](#run-tests-with-coverage)
  - [Manual Testing](#manual-testing)
- [Contributing](#contributing)
- [License](#license)
- [Links](#links)

## Installation

### From RPM (Recommended)

```bash
dnf copr enable quadsdev/python3-quads  -y
dnf install quads-client
```

### From Source

```bash
git clone https://github.com/quadsproject/quads-client.git
cd quads-client
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Configuration

Create `~/.config/quads/quads-client.yml`:

```yaml
servers:
  quads1.rdu2.scalelab:
    url: https://quads1.rdu2.scalelab.example.com
    username: ""
    password: ""
    verify: true

  quads2.rdu2.scalelab:
    url: https://quads2.rdu2.scalelab.example.com
    username: ""
    password: ""
    verify: true

default_server: quads1.rdu2.scalelab
```

**Notes**:
- For new users: Leave `username` and `password` blank. Use the `register` command after connecting to create an account.
- For existing users: Fill in your credentials to login automatically on connect.
- Specify the base URL only (no `/api/v3/` path and no port `:5000`). The QUADS API is accessed via nginx reverse proxy, and quads-lib automatically appends `/api/v3/` to your base URL.
- `verify: true` enables SSL certificate verification using your system's CA bundle (recommended). If you've properly installed your CA certificates via `update-ca-trust` (RHEL/Fedora) or `update-ca-certificates` (Debian/Ubuntu), this will work automatically. Set to `false` only for development/testing with self-signed certificates.

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

### Server Management

```
servers              - List all configured servers with status
add-server <name> <url> <username> <password> [--no-verify]  
                     - Add new server to configuration
edit-server <name> [--url URL] [--username USER] [--password PASS] [--verify true|false]
                     - Edit existing server configuration
rm-server <name>     - Remove server from configuration
config-reload        - Reload configuration from file
```

### Cloud Management

```
cloud-list                         - List all clouds
cloud-list --cloud <name> --detail - Show detailed cloud information with hosts
cloud-create <name>                - Create a new cloud (admin only)
cloud-delete <name>                - Delete a cloud (admin only)
mod-cloud <name> [OPTIONS]         - Modify cloud attributes (admin only)
  --owner OWNER                    - Set cloud owner
  --description DESC               - Set cloud description
  --ticket TICKET                  - Set ticket number
  --wipe true|false                - Enable/disable wipe
  --ccusers CCUSERS                - Set CC users list
```

### Self-Scheduling Mode (SSM)

```
ssm-register <email> <password>              - Register a new user
ssm-login                                     - Explicit login
ssm-whoami                                    - Show current user information
ssm-create --description <desc> [OPTIONS]    - Create a self-assignment
  --wipe true|false                          - Enable/disable wipe
  --qinq <vlan>                              - Set VLAN number
ssm-list                                     - List user's assignments
ssm-status <assignment_id>                   - Show assignment details
ssm-terminate <assignment_id>                - Terminate an assignment
ssm-available                                - Show available hosts for self-scheduling
ssm-schedule <hostname> <cloud>              - Schedule a host for yourself
ssm-my-hosts                                 - Show your scheduled hosts
```

### Host Management (Admin)

```
ls-hosts            - List all hosts
mark-broken <host>  - Mark a host as broken
mark-repaired <host>- Mark a broken host as repaired
retire <host>       - Mark a host as retired
unretire <host>     - Mark a retired host as active
ls-broken           - List all broken hosts
ls-retired          - List all retired hosts
```

### Schedule Management (Admin)

```
ls-schedule [--host hostname] [--cloud cloudname]  - List schedules
add-schedule --host <hostname> --cloud <cloudname> --start <YYYY-MM-DD> --end <YYYY-MM-DD>
mod-schedule --id <schedule_id> [--start <YYYY-MM-DD>] [--end <YYYY-MM-DD>]
rm-schedule <schedule_id>     - Remove a schedule
extend --host <hostname> --weeks <number>  - Extend a schedule
shrink --host <hostname> --weeks <number>  - Shrink a schedule
```

### Available Hosts

```
ls-available [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--model MODEL]
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
- **user**: Can view resources, create schedules, manage assignments, and schedule hosts

When a command requires elevated permissions, the server will return a 403 Forbidden error, which quads-client displays to the user.

### User Registration & Assignments

Users can register accounts directly from the CLI:

1. **Connect** to a server (credentials can be blank in config)
2. **Register** with `register <email> <password>`
3. Credentials are automatically saved to your config file
4. **Login** with the `login` command or reconnect

Assignments allow users to:
- Create self-service cloud assignments with `assignment-create`
- Schedule hosts to their assignments with `schedule`
- View and manage their own resources with `assignment-list`, `my-hosts`
- Terminate assignments when done with `assignment-terminate`

The server controls which hosts can be self-scheduled via the `can_self_schedule` flag.

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

- Python >= 3.13
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
PYTHONPATH=src python3 -c "from quads_client.shell import QuadsClientShell; shell = QuadsClientShell(); shell.cmdloop()"
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

- QUADS Server: https://github.com/quadsproject/quads
- About QUADS: https://quads.dev
- Issues: https://github.com/quadsproject/quads-client/issues
