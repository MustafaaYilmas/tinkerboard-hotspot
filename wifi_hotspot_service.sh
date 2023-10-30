#!/bin/bash

SERVICE_NAME=wifi_connector #your service name
SCRIPT_PATH="/home/linaro/Documents/tinkerboard-hotspot/wifi_hotspot.py" #path your script

echo "[Unit]
Description=WiFi Connector Service
After=network-online.target
Wants=network-online.target

[Service]
ExecStartPre=/bin/sleep 30
ExecStart=/usr/bin/python3 $SCRIPT_PATH
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/$SERVICE_NAME.service

systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME
