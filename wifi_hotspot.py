import os
import subprocess
import time
from flask import Flask, render_template, request, redirect, flash
from werkzeug.serving import make_server

app = Flask(__name__)
app.secret_key = os.urandom(24)

recent_networks = []
server = None  # Flask sunucusunu kontrol etmek için

def is_connected():
    try:
        result = subprocess.run(["sudo", "nmcli", "-t", "con", "show", "--active"], capture_output=True, text=True, check=True)
        active_connections = result.stdout.strip().split('\n')
        return len(active_connections) > 0 and active_connections[0] != ""
    except subprocess.CalledProcessError:
        return False

def set_static_ip():
    os.system("sudo ip addr add 10.0.0.1/24 dev wlan0")

def remove_static_ip():
    os.system("sudo ip addr del 10.0.0.1/24 dev wlan0")


def run_flask_app():
    app.run(host='0.0.0.0', port=5010)

def is_hotspot_active():
    try:
        result = subprocess.run(["sudo", "systemctl", "is-active", "hostapd"], capture_output=True, text=True, check=True)
        return result.stdout.strip() == "active"
    except subprocess.CalledProcessError:
        return False
    
def run_flask_app():
    global server
    server = make_server('0.0.0.0', 5010, app)
    server.serve_forever()

def stop_flask_app():
    if server:
        server.shutdown()
    
def disable_network():
    os.system("sudo systemctl stop NetworkManager")

def enable_network():
    os.system("sudo systemctl start NetworkManager")
    time.sleep(5)  # Ağın başlamasını bekleyelim

def initiate_hotspot():
    set_static_ip()
    disable_network()
    os.system("sudo systemctl start hostapd")

def terminate_hotspot():
    os.system("sudo systemctl stop hostapd")
    remove_static_ip()
    enable_network()

def flask_thread():
    run_flask_app()




def extract_ssid_and_signal(line):
    parts = line.split(":")
    ssid = parts[0]
    signal = parts[1]
    return ssid, signal

def update_recent_networks():
    global recent_networks
    try:
        result = subprocess.run(["sudo", "nmcli", "-t", "-f", "ssid,signal", "device", "wifi", "list"], capture_output=True, text=True, check=True)
        raw_networks = result.stdout.split('\n')[:-1]
        networks = []
        for net in raw_networks:
            ssid, signal = extract_ssid_and_signal(net)
            if ssid and signal:
                networks.append({'ssid': ssid, 'signal': signal})
        recent_networks = networks
    except Exception as e:
        print(f"Error while updating networks: {e}")

@app.route('/')
def index():
    return render_template("wifi_list.html", networks=recent_networks)

@app.route('/connect', methods=['POST'])
def connect():
    ssid = request.form['ssid']
    password = request.form['password']

    if not (1 <= len(ssid) <= 32):
        flash("Invalid SSID.", 'danger')
        return redirect('/')
    if not (8 <= len(password) <= 63):
        flash("Password must be between 8 and 63 characters.", 'danger')
        return redirect('/')

    terminate_hotspot()
    try:
        result = subprocess.run(["sudo", "nmcli", "dev", "wifi", "connect", ssid, "password", password], capture_output=True, text=True, check=True)
        return "<script>window.close();</script>"
    except subprocess.CalledProcessError as e:
        flash(f"Connection error: {e.stderr}", 'danger')
        return redirect('/')

def check_and_maintain_connection():
    while True:
        if not is_connected() and not is_hotspot_active():
            initiate_hotspot()
            
            flask_server_thread = threading.Thread(target=flask_thread)
            flask_server_thread.start()

        elif is_connected():
            terminate_hotspot()
            stop_flask_app()
            update_recent_networks()
        time.sleep(30)

        
if __name__ == '__main__':
    import threading

    update_recent_networks()
    connection_thread = threading.Thread(target=check_and_maintain_connection)
    connection_thread.start()
