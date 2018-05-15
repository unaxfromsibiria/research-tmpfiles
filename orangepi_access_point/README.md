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

### 4) Strange network configuration.

Change for managed=true in /etc/NetworkManager/NetworkManager.conf

My internet provider connect through eth0.

Look at my /etc/network/interfaces

    allow-hotplug eth0
    no-auto-down eth0
    iface eth0 inet dhcp
        hwaddress ether ff:ff:ff:ff:ff:ff
        up sleep 5
        up ifconfig wlan0 inet 10.1.1.1 netmask 255.255.255.0

    iface wlan0 inet manual

    auto lo
    iface lo inet loopback

    iface docker0 inet manual

Yes, it is unexpected usecase. Only this options allow to network apply this ip in wlan0 after reboot.

My congratulations to you if simple static configuration allow you to have ip after reboot.

Another variation of configuration is creation of alias section for wlan0 in /etc/dhcp/dhclient.conf.

### 5) Soft for wifi-router.

Install this:

`aptitude install dnsmasq hostapd dhcpd dhcpcd5`

Change /etc/dhcpcd.conf append line with `denyinterface wlan0`

Edit /etc/hostapd/hostapd.conf as:

    interface=wlan0

    driver=nl80211

    ssid=access-point-name

    hw_mode=g

    channel=6

    ieee80211n=1

    wmm_enabled=1

    ht_capab=[HT40]

    macaddr_acl=0

    auth_algs=1

    ignore_broadcast_ssid=0

    wpa=2

    wpa_key_mgmt=WPA-PSK

    wpa_passphrase=goodpassword

    rsn_pairwise=CCMP

In /etc/default/hostapd change value of DAEMON_CONF to this `DAEMON_CONF="/etc/hostapd/hostapd.conf"`

Edit this configuration /etc/dnsmasq.conf:

    interface=wlan0
    listen-address=10.1.1.1
    bind-interfaces
    server=8.8.8.8
    domain-needed
    bogus-priv
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
    sleep 20 && service dhcpcd restart && service hostapd restart && service dnsmasq restart

And edit /etc/rc.local:

    ....
    /sbin/iptables-restore < /etc/iptables.rules

    /usr/bin/restart-access-point > /tmp/rc.run.log &

    exit 0

### 8) Reboot.

Reboot device several times before disconnecting keyboard and monitor. Make sure the ip address in interface is configured.
