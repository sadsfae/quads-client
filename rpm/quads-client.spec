#### NOTE: if building locally you may need to do the following:
####
#### yum install rpmdevtools -y
#### spectool -g -R rpm/quads-client.spec
####
#### At this point you can use rpmbuild -ba quads-client.spec
#### this is because our Source0 is a remote Github location
####
#### Our upstream repository is located here:
#### https://copr.fedorainfracloud.org/coprs/quadsdev/quads-client
####

%define name quads-client
%define reponame quads-client
%define branch main
%define version 0.2.0
%define build_timestamp %{lua: print(os.date("%Y%m%d"))}

Summary: QUADS Client TUI Shell for managing multiple QUADS server instances
Name: %{name}
Version: %{version}
Release: %{build_timestamp}
Source0: https://github.com/sadsfae/quads-client/archive/%{branch}.tar.gz#/%{name}-%{version}-%{release}.tar.gz
License: GPLv3
BuildRoot: %{_tmppath}/%{name}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: QUADS Project
Packager: QUADS Project
BuildRequires: python3-devel >= 3.13
BuildRequires: python3-setuptools
Requires: python3 >= 3.13
Requires: python3-cmd2 >= 2.0.0
Requires: quads-lib >= 0.1.9
Requires: python3-tabulate >= 0.9.0
Requires: python3-argcomplete >= 3.1.2
Requires: python3-PyYAML >= 6.0.0
Requires: python3-jwt >= 2.8.0
Requires: python3-rich >= 13.0.0
Requires: python3-requests >= 2.31.0
Requires: python3-urllib3 >= 2.0.0
Requires: bash-completion

AutoReq: no

Url: https://quads.dev

%description

QUADS Client is an interactive TUI (Text User Interface) shell for managing
multiple QUADS (QUADS Automated Deployment System) server instances.

Features include:
 * Multi-server connection management with bearer token authentication
 * Interactive cmd2-based shell with command history and tab completion
 * Self-scheduling mode (SSM) for non-admin users
 * Cloud management commands (list, create, delete)
 * Real-time provisioning progress tracking
 * SQLite-based persistent command history
 * Thin wrapper design with server-side authorization

QUADS Client requires Python 3.13 or later and communicates with QUADS
servers via the python-quads-lib API wrapper.

%prep
%autosetup -n %{reponame}-%{branch}

%build
%py3_build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_datadir}/doc/quads-client
%py3_install

# Install example configuration
install -m 0644 conf/quads-client.yml.example %{buildroot}%{_datadir}/doc/quads-client/

%clean
rm -rf %{buildroot}

%files
%doc README.md
%license LICENSE
%{_bindir}/quads-client
%{python3_sitelib}/quads_client/
%{python3_sitelib}/quads_client-*.egg-info/
%{_datadir}/doc/quads-client/

%post
# Enable bash completion globally if available
if [ -x /usr/bin/activate-global-python-argcomplete3 ]; then
    /usr/bin/activate-global-python-argcomplete3 2>/dev/null || true
fi

# First time installation message
if [ "$1" -eq 1 ]; then
echo "======================================================="
echo " QUADS Client installed successfully                   "
echo "======================================================="
echo "                                                       "
echo " To get started:                                       "
echo "   1. Copy example config:                             "
echo "      cp /usr/share/doc/quads-client/quads-client.yml.example ~/.quads-client.yml"
echo "   2. Edit ~/.quads-client.yml with your QUADS servers "
echo "   3. Run: quads-client                                "
echo "                                                       "
echo "======================================================="
fi
:;

%preun
:;

%postun
find %{python3_sitelib}/quads_client 2>/dev/null | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf 2>/dev/null || true
:;

%changelog

* Wed Apr 30 2026 Will Foster <wfoster@redhat.com>
- 1.0.0 initial release
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
