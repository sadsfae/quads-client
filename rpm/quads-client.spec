Name:           quads-client
Version:        1.0.0
Release:        1%{?dist}
Summary:        QUADS Client TUI Shell

License:        GPLv3
URL:            https://quads.dev
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel >= 3.13
BuildRequires:  python3-setuptools

# Runtime dependencies
Requires:       python3 >= 3.13
Requires:       python3-cmd2 >= 2.0.0
Requires:       quads-lib >= 0.1.9
Requires:       python3-tabulate >= 0.9.0
Requires:       python3-argcomplete >= 3.1.2
Requires:       python3-pyyaml >= 6.0.0
Requires:       bash-completion

%description
QUADS Client is an interactive TUI (Text User Interface) shell for managing
multiple QUADS (QUADS Automated Deployment System) server instances.

Features:
- Multi-server connection management with bearer token authentication
- Interactive cmd2-based shell with command history and tab completion
- Self-scheduling mode (SSM) for non-admin users
- Cloud management commands (list, create, delete)
- Real-time provisioning progress tracking
- SQLite-based persistent command history
- Thin wrapper design with server-side authorization

QUADS Client requires Python 3.13 or later and communicates with QUADS
servers via the python-quads-lib API wrapper.

%prep
%autosetup -n quads_client-%{version}

%build
%py3_build

%install
%py3_install

# Install example configuration
mkdir -p %{buildroot}%{_datadir}/doc/quads-client
install -m 0644 conf/quads-client.yml.example %{buildroot}%{_datadir}/doc/quads-client/

%files
%license LICENSE
%doc README.md
%{_bindir}/quads-client
%{python3_sitelib}/quads_client/
%{python3_sitelib}/quads_client-*.egg-info/
%{_datadir}/doc/quads-client/

%post
# Enable bash completion globally if available
if [ -x /usr/bin/activate-global-python-argcomplete3 ]; then
    /usr/bin/activate-global-python-argcomplete3 || true
fi

%changelog
* Thu Apr 30 2026 Will Foster <wfoster@redhat.com> - 1.0.0-1
- Initial quads-client package release
- TUI shell with multi-server support
- Thin wrapper design with server-side authorization
- Self-scheduling mode (SSM) for non-admin users
- Real-time provisioning progress tracking
- SQLite-based persistent command history
- Python 3.13+ requirement
- Removed PyJWT dependency (server handles token validation)
- Black formatted code (line-length 119)
- Comprehensive test suite (44 tests, 61%% coverage)
- Cloud management commands (list, create, delete)
- Connection management (connect, disconnect, status)
- Bearer token authentication via python-quads-lib
