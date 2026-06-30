#!/bin/sh
grep -rwl '8006' /usr/share/perl5/PVE/ | xargs sed -i 's|8006|443|g'
grep -rwl '8006' /usr/share/pve-docs/ | xargs sed -i 's|:8006||g'
grep -rwl '8006' /usr/share/pve-docs/ | xargs sed -i 's|8006|443|g'
grep -rwl '8006' /usr/share/doc/pve-manager/ | xargs sed -i 's|:8006||g'
sed -i 's|:8006||g' /usr/bin/pvebanner
sed -i 's|:8006||g' /etc/issue
echo 'net.ipv4.ip_unprivileged_port_start=0' > /etc/sysctl.d/50-unprivileged-ports.conf
reboot