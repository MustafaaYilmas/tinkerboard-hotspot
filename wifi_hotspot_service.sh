#!/bin/bash

SERVICE_NAME=wifi_connector #your service name
SCRIPT_PATH="/home/linaro/Desktop/tinkerboard-hotspot/wifi_hotspot.py" #path your script

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
Environment=PYTHONUNBUFFERED=1 PYTHONPATH=/home/linaro:/usr/local/lib/python3.7/site-packages:/usr/lib/python37.zip:/usr/lib/python3.7:/usr/lib/python3.7/lib-dynload:/home/linaro/.local/lib/python3.7/site-packages:/usr/local/lib/python3.7/dist-packages:/usr/lib/python3/dist-packages

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/$SERVICE_NAME.service

systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME
