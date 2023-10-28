import os
import subprocess
import time
import threading
from flask import Flask, render_template, request, redirect, flash
from werkzeug.serving import make_server

MAX_RETRIES = 3
RETRY_WAIT_TIME = 10  # saniye
server_thread_started = False

app = Flask(__name__)
app.secret_key = os.urandom(24)

recent_networks = []
server = None

def execute_command(command_list, get_output=False):
    try:
        if get_output:
            result = subprocess.run(command_list, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        else:
            subprocess.run(command_list, check=True)
            return True
    except subprocess.CalledProcessError:
        return False

def is_connected():
    output = execute_command(["sudo", "nmcli", "-t", "con", "show", "--active"], True)
    if output:
        active_connections = output.split('\n')
        return len(active_connections) > 0 and active_connections[0] != ""
    return False

def is_hotspot_active():
    return execute_command(["sudo", "systemctl", "is-active", "hostapd"], True) == "active"

def set_ip_address(action="add"):
    cmd = "add" if action == "add" else "del"
    execute_command(["sudo", "ip", "addr", cmd, "10.0.0.1/24", "dev", "wlan0"])

def control_network_manager(action="start"):
    execute_command(["sudo", "systemctl", action, "NetworkManager"])
    if action == "start":
        time.sleep(5)  # Give network time to initialize

def ensure_hostapd_active():
    retries = 0
    while retries < MAX_RETRIES:
        if not is_hotspot_active():
            print("hostapd is not active. Retrying...")
            execute_command(["sudo", "systemctl", "stop", "hostapd"])
            time.sleep(RETRY_WAIT_TIME)
            execute_command(["sudo", "systemctl", "start", "hostapd"])
            retries += 1
        else:
            print("hostapd is active.")
            return True
    print(f"Failed to start hostapd after {MAX_RETRIES} retries.")
    return False


def initiate_hotspot():
    set_ip_address("add")
    control_network_manager("stop")
    execute_command(["sudo", "systemctl", "start", "hostapd"])
    ensure_hostapd_active()

def terminate_hotspot():
    execute_command(["sudo", "systemctl", "stop", "hostapd"])
    set_ip_address("del")
    control_network_manager("start")

def update_recent_networks():
    global recent_networks
    output = execute_command(["sudo", "nmcli", "-t", "-f", "ssid,signal", "device", "wifi", "list"], True)
    if output:
        raw_networks = output.split('\n')[:-1]
        networks = [{'ssid': net.split(':')[0], 'signal': net.split(':')[1]} for net in raw_networks if net]
        recent_networks = networks

@app.route('/')
def index():
    return render_template("wifi_list.html", networks=recent_networks)

@app.route('/connect', methods=['POST'])
def connect():
    ssid = request.form['ssid']
    password = request.form['password']

    if not (1 <= len(ssid) <= 32) or not (8 <= len(password) <= 63):
        flash("Invalid SSID or password length.", 'danger')
        return redirect('/')

    terminate_hotspot()

    if execute_command(["sudo", "nmcli", "dev", "wifi", "connect", ssid, "password", password]):
        return "<script>window.close();</script>"
    else:
        flash("Connection error.", 'danger')
        return redirect('/')

def check_and_maintain_connection():
    global server_thread_started

    while True:
        if not is_connected() and not is_hotspot_active():
            initiate_hotspot()

            if not server_thread_started:
                flask_server_thread = threading.Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 5010})
                flask_server_thread.start()
                server_thread_started = True

            update_recent_networks()

        elif is_connected() and is_hotspot_active():
            terminate_hotspot()
        time.sleep(300)  # Checking every 5 minutes



if __name__ == '__main__':
    update_recent_networks()
    connection_thread = threading.Thread(target=check_and_maintain_connection)
    connection_thread.start()
