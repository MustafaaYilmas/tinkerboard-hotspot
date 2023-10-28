
# WiFi Connection Manager

## Overview
This script provides a WiFi connection manager that runs on a Flask web server. The purpose is to check for an active WiFi connection. If none exists, it sets up a hotspot so that a user can connect and select a WiFi network to connect to. The Flask web server provides an interface for the user to view available WiFi networks and connect to them.

## Prerequisites
- Python 3
- Flask
- nmcli (NetworkManager Command Line Interface)
- hostapd (Linux software to create a hotspot)
- bash (for executing setup and service scripts)
- Systemd (for managing the service)

## Features

### Hotspot Management
The script ensures that a hotspot is initiated if no active WiFi connections are detected. If the hotspot is not active, the script will attempt to restart it a few times (determined by the `MAX_RETRIES` constant) before giving up.

### Network Scan
The script uses `nmcli` to scan for available WiFi networks and displays them in the Flask web server interface.

### Network Connection
Users can select a network and input the WiFi password to connect to the chosen network. If the connection fails, the user will be notified.

### Automatic Connection Checking
The script constantly checks (every 5 minutes by default) whether there's an active WiFi connection. If a connection is detected, the hotspot will be terminated.

## Routes
- `/` - Displays the list of available WiFi networks.
- `/connect` - Endpoint to connect to a selected WiFi network using the provided password.

## Installation and Configuration

1. Run the `setup.sh` script to install the required packages and configure the system:

```bash
$ sudo ./setup.sh
```

This script will:
- Install `hostapd` if it's not already installed.
- Configure `hostapd` with specified settings for the hotspot.
- Install `ufw` (a firewall) if it's not installed and open port 5010.
- Install `dnsmasq` if it's not installed and configure it for the hotspot.
- Reload the systemd daemon and restart `dnsmasq`.

## Running as a Service

To run the WiFi Connection Manager as a service, execute the `wifi_hotspot_service.sh` script:

```bash
$ sudo ./wifi_hotspot_service.sh
```

This script will:
- Create a new systemd service for the WiFi Connection Manager.
- Reload the systemd daemon.
- Enable the service to start on boot.
- Start the service immediately.

**Note**: Make sure to adjust the `SCRIPT_PATH` variable in `wifi_hotspot_service.sh` to the correct path of your `wifi_hotspot.py` script.

## How to Use

1. Ensure all prerequisites are installed and properly configured.
2. Run the script. It will automatically check for an active WiFi connection.
3. If no active connection is detected, the script will initiate a hotspot.
4. Connect to the hotspot from a device.
5. Open a web browser and navigate to the Flask web server (default: `http://10.0.0.1:5010/`).
6. Select a WiFi network, input the password, and click "Connect".

