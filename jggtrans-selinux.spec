%define selinux_variants mls strict targeted 
%define selinux_policyver %(sed -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp 2> /dev/null)
%define moduletype apps
%define modulename jggtrans

Name:            jggtrans-selinux
Version:         0.3
Release:         1%{?dist}
Summary:         SELinux policy module supporting jggtrans
Group:           System Environment/Base
License:         GPLv2+
URL:             http://yum.ertel.com.pl
Source1:         %{modulename}.if
Source2:         %{modulename}.te
Source3:         %{modulename}.fc
Source4:         %{name}-enable
BuildRoot:       %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildRequires:   checkpolicy, selinux-policy-devel, hardlink
BuildArch:       noarch

%if "%{selinux_policyver}" != ""
Requires:         selinux-policy >= %{selinux_policyver}
%endif
Requires(post):   /usr/sbin/semodule, /sbin/restorecon, /sbin/ldconfig, /usr/sbin/selinuxenabled
Requires(postun): /usr/sbin/semodule, /sbin/restorecon

%description
SELinux policy module supporting jggtrans.

%prep
rm -rf %{name}-%{version}
mkdir -p %{name}-%{version}
cp -p %{SOURCE1} %{SOURCE2} %{SOURCE3} %{SOURCE4} %{name}-%{version}

%build
# Build SELinux policy modules
cd %{name}-%{version}
perl -i -pe 'BEGIN { $VER = join ".", grep /^\d+$/, split /\./, "%{version}.%{release}"; } s!\@\@VERSION\@\@!$VER!g;' %{modulename}.te
for selinuxvariant in %{selinux_variants}
do
    make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
    mv %{modulename}.pp %{modulename}.pp.${selinuxvariant}
    make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -

%install
rm -rf %{buildroot}

# Install SELinux policy modules
cd %{name}-%{version}
for selinuxvariant in %{selinux_variants}
  do
    install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
    install -p -m 644 %{modulename}.pp.${selinuxvariant} \
           %{buildroot}%{_datadir}/selinux/${selinuxvariant}/%{modulename}.pp
  done

cd -

# Install SELinux interfaces
install -d %{buildroot}%{_datadir}/selinux/devel/include/%{moduletype}
install -p -m 644 %{name}-%{version}/%{modulename}.if \
  %{buildroot}%{_datadir}/selinux/devel/include/%{moduletype}/%{modulename}.if

# Hardlink identical policy module packages together
/usr/sbin/hardlink -cv %{buildroot}%{_datadir}/selinux

# Install jggtrans-selinux-enable which will be called in %posttrans
install -d %{buildroot}%{_sbindir}
install -p -m 755 %{name}-%{version}/%{name}-enable %{buildroot}%{_sbindir}/%{name}-enable

%clean
rm -rf %{buildroot}

%post
if /usr/sbin/selinuxenabled ; then
   %{_sbindir}/%{name}-enable
fi

%posttrans
#this may be safely remove when BZ 505066 is fixed
if /usr/sbin/selinuxenabled ; then
  # Relabel jggtrans's files
#  rpm -ql jggtrans | xargs -n 100 /sbin/restorecon -Rivv
/sbin/restorecon -F -R -v /usr/sbin/jggtrans
/sbin/restorecon -F -R -v /etc/rc.d/init.d/jggtrans
/sbin/restorecon -F -R -v /etc/sysconfig/jggtrans
/sbin/restorecon -F -R -v /var/lib/jggtrans
fi

%postun
# Clean up after package removal
if [ $1 -eq 0 ]; then
  # Remove SELinux policy modules
  for selinuxvariant in %{selinux_variants}
    do
      /usr/sbin/semodule -s ${selinuxvariant} -r %{modulename} &> /dev/null || :
    done


/sbin/restorecon -F -R -v /usr/sbin/jggtrans
/sbin/restorecon -F -R -v /etc/rc.d/init.d/jggtrans
/sbin/restorecon -F -R -v /etc/sysconfig/jggtrans
/sbin/restorecon -F -R -v /var/lib/jggtrans
fi

%files
%defattr(-,root,root,0755)
%doc %{name}-%{version}/%{modulename}.fc %{name}-%{version}/%{modulename}.if %{name}-%{version}/%{modulename}.te
%{_datadir}/selinux/*/%{modulename}.pp
%{_datadir}/selinux/devel/include/%{moduletype}/%{modulename}.if
%attr(0755,root,root) %{_sbindir}/%{name}-enable

%changelog
* Mon Aug 20 2009 Adam Przybyla 0.1
- Initial version
