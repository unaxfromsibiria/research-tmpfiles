## Access point counfiguration for Orangepi PC Plus.

### 1) Download and record image of Armbian.

Choise your model in this download page https://www.armbian.com/download/?tx_maker=xunlong

Unfortunately I haven't created stable network configuration in this OS. And I have tried different configurations to get access point with fresh packages.

I tried other OS, but problems was worse with them.

Ok, writing the image into card (be careful with out device):

`dd bs=1M if=./<path>/Armbian_5.38_Orangepipcplus_Debian_stretch_next_4.14.14.img iflag=fullblock oflag=direct of=/dev/mmcblk0`

You can use Gparted to stretch free space of slice with OS.

### 2) Run and update.

Load OS and enter to shell. Check the wifi device. Install updates:

`aptitude update && aptitude full-upgrade`

### 3) Docker.

Install the docker by this document https://www.raspberrypi.org/blog/docker-comes-to-raspberry-pi/

    # docker version
    Client:
    Version:      18.05.0-ce
    API version:  1.37
    Go version:   go1.9.5
    Git commit:   f150324
    Built:        Wed May  9 22:24:18 2018
    OS/Arch:      linux/arm
    Experimental: false
    Orchestrator: swarm

    Server:
    Engine:
    Version:      18.05.0-ce
    API version:  1.37 (minimum version 1.12)
    Go version:   go1.9.5
    Git commit:   f150324
    Built:        Wed May  9 22:20:22 2018
    OS/Arch:      linux/arm
    Experimental: false

### 4) Quite simple network configuration.

Make sure that option is managed=false in /etc/NetworkManager/NetworkManager.conf

My internet provider connection through eth0 with MAC from my old wi-fi router.

Look at my /etc/network/interfaces

    allow-hotplug eth0
    iface eth0 inet manual
        hwaddress ether 00:40:f4:b1:c3:94

    auto lo
    iface lo inet loopback

Write nothing about wlan0 docker0.

### 5) Soft for wifi-router.

At first you should to remove dhcp clients:

`aptitude remove isc-dhcp-client isc-dhcp-common udhcpd`

Install this:

`aptitude install dnsmasq hostapd dhcpd dhcpcd5`

We will create settings of local wi-fi network in /etc/dhcpcd.conf
 
    interface wlan0
        static ip_address=10.1.1.1/24

Edit /etc/hostapd/hostapd.conf as:

    interface=wlan0
    driver=nl80211
    ssid=name
    hw_mode=g
    channel=2
    ieee80211n=1
    wmm_enabled=0
    macaddr_acl=0
    auth_algs=1
    ignore_broadcast_ssid=0
    wpa=2
    wpa_key_mgmt=WPA-PSK
    wpa_passphrase=access password!
    rsn_pairwise=CCMP
    wpa_pairwise=TKIP

In /etc/default/hostapd change value of DAEMON_CONF to this `DAEMON_CONF="/etc/hostapd/hostapd.conf"`

Edit this configuration /etc/dnsmasq.conf:

    interface=wlan0
    listen-address=10.1.1.1
    server=8.8.8.8
    dhcp-range=10.1.1.100,10.1.1.250,12h

Disable those services:

    systemctl disable dnsmasq
    systemctl disable hostapd
    systemctl disable dhcpcd

### 6) Iptable and forwarding.

Change /etc/sysctl.conf remove '#' from the line whih net.ipv4.ip_forward=1

Create iptable rules:

    iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
    iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
    iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT

And save it: `iptables-save > /etc/iptables.rules`

### 7) Autostart.

Create script `touch /usr/bin/restart-access-point.sh && chmod 750 /usr/bin/restart-access-point.sh`

with this content:

    #!/bin/bash
    sleep 15 && service dhcpcd restart && service hostapd restart && service dnsmasq restart

And edit /etc/rc.local:

    ....
    /sbin/iptables-restore < /etc/iptables.rules

    /usr/bin/restart-access-point > /tmp/rc.run.log &

    exit 0

### 8) Reboot.

Reboot device several times before disconnecting keyboard and monitor. Make sure the ip address in interface is configured.
