#!/bin/bash

# 1. hostapd setup check
if ! command -v hostapd &> /dev/null; then
    apt-get update
    apt-get install -y hostapd
fi

# 2. config file for hostapd
HOSTAPD_CONF="/etc/hostapd/hostapd.conf"
if [ -f "$HOSTAPD_CONF" ]; then
    rm -f "$HOSTAPD_CONF"
fi
cat <<EOL > $HOSTAPD_CONF
interface=wlan0
ssid=AgedAiNetwork
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=agedai123.
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOL

# 3. hostapd stop
sudo systemctl stop hostapd

# 4. ufw setup check
if ! command -v ufw &> /dev/null; then
    apt-get update
    apt-get install -y ufw
fi

# 5. open port 5010 with ufw
ufw allow 5010/tcp

# 6. dnsmasq setup check
if ! command -v dnsmasq &> /dev/null; then
    apt-get update
    apt-get install -y dnsmasq
fi

# 7. Adding values to dnsmasq.conf
DNSMASQ_CONF="/etc/dnsmasq.conf"
echo "interface=wlan0" >> $DNSMASQ_CONF
echo "dhcp-range=10.0.0.2,10.0.0.16,255.255.255.0,24h" >> $DNSMASQ_CONF

# 8. adding the value port=5353
echo "port=5353" >> $DNSMASQ_CONF

#9. daemon -reload
sudo systemctl daemon-reload

pip3 install --user flask
# 10. dnsmasq reboot
sudo systemctl restart dnsmasq
