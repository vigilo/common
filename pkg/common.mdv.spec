%define module  common
%define name    vigilo-%{module}
%define version 1.0
%define release 1

Name:       %{name}
Summary:    Vigilo common library
Version:    %{version}
Release:    %{release}
Source0:    %{module}.tar.bz2
URL:        http://www.projet-vigilo.org
Group:      System/Servers
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-build
License:    GPLv2

BuildRequires:   python-setuptools

Requires:   python >= 2.5
Requires:   python-setuptools
Requires:   configobj

Buildarch:  noarch


%description
This library provides common facilities to Vigilo components, such as
configuration loading, logging, daemonizing, i18n, etc.
This library is part of the Vigilo Project <http://vigilo-project.org>

%prep
%setup -q -n %{module}

%build
make PYTHON=%{_bindir}/python

%install
rm -rf $RPM_BUILD_ROOT
make install \
	DESTDIR=$RPM_BUILD_ROOT \
	PREFIX=%{_prefix} \
	PYTHON=%{_bindir}/python


%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc COPYING


%changelog
* Mon Feb 08 2010 Aurelien Bompard <aurelien.bompard@c-s.fr> - 1.0-1
- initial package
