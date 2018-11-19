%define gitver 0ab3473
%define srcname nmstate
%define libname libnmstate

Name:           nmstate
Version:        0.0.1
Release:        0.git%{gitver}%{?dist}
Summary:        Declarative network manager API
Group:          System Environment/Libraries
License:        GPLv2+
URL:            https://github.com/%{srcname}/%{srcname}
Source0:        https://github.com/%{srcname}/%{srcname}/archive/v%{version}/%{srcname}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python2-devel
BuildRequires:  python2-six
BuildRequires:  python2-pyyaml
BuildRequires:  python-jsonschema
BuildRequires:  python-pbr
BuildRequires:  python-setuptools
Requires:       python2-%{libname}

%description
NMState is a library with an accompanying command line tool that manages host
networking settings in a declarative manner and aimed to satisfy enterprise
needs to manage host networking through a northbound declarative API and multi
provider support on the southbound.


%package -n python2-%{libname}
Summary:        nmstate python API library
Group:          System Environment/Libraries
License:        GPLv2+
Requires:       NetworkManager-libnm
Requires:       python-gobject
Requires:       python2-six
Requires:       python-jsonschema
Requires:       python2-pyyaml

%description -n python2-%{libname}
This package contains the python library for nmstate.

%prep
%setup -q -n %{srcname}-%{version}

%build
PBR_VERSION="%{version}" %py2_build

%install
PBR_VERSION="%{version}" %py2_install
install -D libnmstate/schemas/operational-state.yaml \
    %{buildroot}/%{python2_sitelib}/%{libname}/schemas/operational-state.yaml

%files
%doc README.md
%license LICENSE
%{python2_sitelib}/nmstatectl
%{_bindir}/nmstatectl

%files -n python2-%{libname}
%{python2_sitelib}/%{libname}
%{python2_sitelib}/%{srcname}-*.egg-info/

%changelog
* Mon Nov 19 2018 Gris Ge <fge@redhat.com> - 0.0.1-1
- Initial release.
