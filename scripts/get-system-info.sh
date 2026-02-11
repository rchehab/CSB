#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

set -e

[ -z "$1" ] && exit 1

mkdir -p "$1"

hostname > "$1"/hostname.txt
ip a s > "$1"/ipaddress.txt
/sbin/sysctl -a > "$1"/sysctl.txt
cat /proc/cmdline > "$1"/kcmdline.txt
uname -a > "$1"/uname.txt
cat /proc/loadavg > "$1"/loadavg.txt
cat /proc/interrupts > "$1"/interrupts.txt
cat /proc/modules > "$1"/modules.txt
mount > "$1"/mount.txt

if command -v lscpu >/dev/null 2>/dev/null; then
    lscpu > "$1"/cpu.txt
else
    echo "lscpu not available, skipping!" > /dev/stderr
fi

if command -v lshw >/dev/null 2>/dev/null; then
    lshw > "$1"/hw.txt
else
    echo "lshw not available, skipping!" > /dev/stderr
fi

find /proc/irq/ -maxdepth 1 -mindepth 1 -type d | while read -r i; do
    printf '%s ' "${i#/proc/irq/}";
    cat "$i/smp_affinity"
done > "$1"/interrupt-affinity.txt

if command -v cgsnapshot >/dev/null 2>/dev/null; then
    cgsnapshot 2>&1 > "$1"/cgroups.txt | awk '/WARNING/ {print} /ERROR/ {$1 = ""; print "WARNING:"$0}'
else
    echo "cgsnapshot not available, skipping!" > /dev/stderr
fi

if command -v ethtool >/dev/null 2>/dev/null; then
    for i in /sys/class/net/*; do
	nic="${i#/sys/class/net/}"
	ethtool -g "$nic" 2> /dev/null || echo "WARNING: Cannot read rx/tx ring for NIC ${nic}" > /dev/stderr
	ethtool -l "$nic" 2> /dev/null || echo "WARNING: Cannot read number of channels for NIC ${nic}" > /dev/stderr
	ethtool -n "$nic" 2> /dev/null || echo "WARNING: Cannot read network flow options for NIC ${nic}" > /dev/stderr

    done > "$1"/nics.txt
else
    echo "ethtool not available, skipping!" > /dev/stderr
fi

if command -v nvme-cli >/dev/null 2>/dev/null; then
    nvme-cli list > "$1"/nvme.txt
elif command -v nvme >/dev/null 2>/dev/null; then
    modprobe nvme_core || true # the version in openeuler fails to work without the module loaded.
    nvme list > "$1"/nvme.txt
else
    echo "nvme-cli not available, skipping!" > /dev/stderr
fi

if command -v docker >/dev/null 2>/dev/null; then
    docker --version > "$1"/docker-version.txt
fi

if [ -e "/etc/os-release" ]; then
    cat /etc/os-release > "$1"/os-release.txt
fi

if command -v hdparm >/dev/null 2>/dev/null; then
    # if no match for /dev/sd[a-z] is found
    # return an empty list instead of /dev/sd[a-z]
    shopt -s nullglob
    for i in /dev/sd[a-z]; do
        hdparm "$i"
    done > "$1"/hdds.txt
    # undo the setting
    shopt -u nullglob
else
    echo "hdparm not available, skipping!" > /dev/stderr
fi

if [ -e "/proc/config.gz" ]; then
    zcat /proc/config.gz > "$1"/kconfig.txt
elif [ -e /boot/config-"$(uname -r)" ]; then
    cp /boot/config-"$(uname -r)" "$1"/kconfig.txt
elif [ -n "$2" ] && [ -f "$2" ]; then
    cp "$2" "$1"/kconfig.txt
else
    echo "Kernel .config not available!" > /dev/stderr
fi
