import os
import subprocess
import time
import threading
from flask import Flask, render_template, request, redirect, flash

MAX_RETRIES = 10
RETRY_WAIT_TIME = 10  # seconds
CONNECTION_STABILITY_TIME = 60  # seconds
server_thread_started = False

app = Flask(__name__)
app.secret_key = os.urandom(24)

recent_networks = []

# Function to set IP address for wlan0 interface
def set_ip_address(action="add"):
    cmd = "add" if action == "add" else "del"
    execute_command(["sudo", "ip", "addr", cmd, "10.0.0.1/24", "dev", "wlan0"])

# Execute shell command and optionally return the output
def execute_command(command_list, get_output=False):
    try:
        if get_output:
            result = subprocess.run(command_list, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        else:
            subprocess.run(command_list, check=True)
            return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command {' '.join(command_list)}: {str(e)}")
        return False

# Check if there's an active network connection
def is_connected():
    try:
        output = execute_command(["sudo", "nmcli", "-t", "con", "show", "--active"], True)
        print(output)
        return bool(output)
    except Exception as e:
        print(f"Error checking connection status: {str(e)}")
        return False

# Check if the hotspot is currently active
def is_hotspot_active():
    try:
        result = execute_command(["sudo", "systemctl", "is-active", "hostapd"], True) == "active"
        print(result)
        return result
    except Exception as e:
        print(f"Error checking hotspot status: {str(e)}")
        return False

# Control the NetworkManager service based on the given action (e.g., start, stop, restart)
def control_network_manager(action="restart"):
    try:
        execute_command(["sudo", "systemctl", action, "NetworkManager"])
        if action in ["start", "restart"]:
            time.sleep(5)  # Give network time to initialize
    except Exception as e:
        print(f"Error controlling NetworkManager: {str(e)}")

# Start the hotspot by configuring the necessary services
def initiate_hotspot():
    try:
        control_network_manager("stop")
        set_ip_address("add") 
        execute_command(["sudo", "systemctl", "start", "hostapd"])
    except Exception as e:
        print(f"Error initiating hotspot: {str(e)}")

# Terminate the hotspot and return to the standard network connection
def terminate_hotspot():
    try:
        execute_command(["sudo", "systemctl", "stop", "hostapd"])
        control_network_manager("start")
        set_ip_address("del")
        # if is_connection_stable():
        #     execute_command(["sudo", "systemctl", "restart", "aged-ai.service"])
    except Exception as e:
        print(f"Error terminating hotspot: {str(e)}")

# Check if the network connection remains stable for a defined period
def is_connection_stable():
    try:
        start_time = time.time()
        while time.time() - start_time < CONNECTION_STABILITY_TIME:
            if not is_connected():
                return False
            time.sleep(5)  # check every 5 seconds
        return True
    except Exception as e:
        print(f"Error checking connection stability: {str(e)}")
        return False

# Update the list of recent networks
def update_recent_networks():
    global recent_networks
    try:
        output = execute_command(["sudo", "nmcli", "-t", "-f", "ssid,signal", "device", "wifi", "list"], True)
        if output:
            raw_networks = output.split('\n')[:-1]
            #print(raw_networks)
            networks = [{'ssid': net.split(':')[0], 'signal': net.split(':')[1]} for net in raw_networks if net]
            recent_networks = networks

            #print(recent_networks)
    except Exception as e:
        print(f"Error updating recent networks: {str(e)}")

# Endpoint to display available networks
@app.route('/')
def index():
    update_recent_networks()
    return render_template("wifi_list.html", networks=recent_networks)

# Endpoint to connect to a specific network
@app.route('/connect', methods=['POST'])
def connect():
    try:
        ssid = request.form['ssid']
        password = request.form['password']

        if not (1 <= len(ssid) <= 32) or not (8 <= len(password) <= 63):
            flash("Invalid SSID or password length.", 'danger')
            return redirect('/')

        terminate_hotspot()

        if execute_command(["sudo", "nmcli", "dev", "wifi", "connect", ssid, "password", password]):
            execute_command(["sudo", "systemctl", "restart", "aged-ai.service"])
            return "<script>window.close();</script>"
        else:
            flash("Connection error.", 'danger')
            return redirect('/')
    except Exception as e:
        flash(f"Unexpected error: {str(e)}", 'danger')
        return redirect('/')

# Initialize the first network connection or switch to hotspot if unable to connect
def first_init_connection():
    try:
        update_recent_networks()
        if not is_connected():
            
            control_network_manager("stop")

            
            set_ip_address("add")

            
            execute_command(["sudo", "systemctl", "restart", "hostapd"])

            
            if is_connected():

                execute_command(["sudo", "systemctl", "stop", "hostapd"])
                if is_connection_stable():
                        execute_command(["sudo", "systemctl", "restart", "aged-ai.service"])
            else:

                execute_command(["sudo", "systemctl", "stop", "hostapd"])
        else:
            update_recent_networks()
            execute_command(["sudo", "systemctl", "stop", "hostapd"])
            execute_command(["sudo", "systemctl", "restart", "NetworkManager"])
            time.sleep(5)
            execute_command(["sudo", "systemctl", "restart", "aged-ai.service"])
    except Exception as e:
        print(f"Bir hata oluştu: {e}")


    
# Continuously check and maintain network connection; switch between regular network and hotspot as needed
def check_and_maintain_connection():

    global server_thread_started 

    if not server_thread_started:
        flask_server_thread = threading.Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 5010})
        flask_server_thread.start()
        server_thread_started = True

    previously_connected = False

    first_init_connection()


    while True:
        try:
            currently_connected = is_connected()
            print("baglanti durumu ", currently_connected)
            update_recent_networks()

            # Eğer şu anda bağlıysak
            if currently_connected:
                # Hotspot kontrolü
                if is_hotspot_active():
                    print("Cihaz bağlıyken hotspot aktif! Hotspot kapatılıyor...")
                    # IP adresini değiştirmeden sadece hotspot'u kapatma işlemi gerçekleştir
                    execute_command(["sudo", "systemctl", "stop", "hostapd"])

            # Eğer şu anda bağlı değilse
            else:
                if not is_hotspot_active():
                    update_recent_networks()
                    print("hotspot aktif degilse")
                    initiate_hotspot()
                    print("hotspot acildi")

            previously_connected = currently_connected
            time.sleep(30)
        except Exception as e:
            print(f"Error in check_and_maintain_connection loop: {str(e)}")
            time.sleep(60)  # If an error occurs, wait a minute before trying



if __name__ == "__main__":
    check_and_maintain_connection()
