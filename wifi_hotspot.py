import os
import subprocess
import threading
from flask import Flask, render_template, request, redirect, flash
from pydbus import SystemBus
from werkzeug.serving import run_simple

app = Flask(__name__)
app.secret_key = os.urandom(24)
check_interval = 60  # Kontrol aralığı (saniye)

def is_connected():
    bus = SystemBus()
    nm = bus.get(".NetworkManager", "/org/freedesktop/NetworkManager")
    state = nm.State
    return state == 70

def run_flask_app():
    run_simple('0.0.0.0', 5000, app)

def check_network():
    if is_connected():
        print("Bağlantı başarılı!")
    else:
        print("Bağlantı kesildi!")
        os.system("sudo systemctl start hostapd")
        flask_thread = threading.Thread(target=run_flask_app)
        flask_thread.start()

    threading.Timer(check_interval, check_network).start()

@app.route('/')
def index():
    try:
        result = subprocess.run(["sudo", "nmcli", "device", "wifi", "list"], capture_output=True, text=True, check=True)
        networks = result.stdout.split('\n')[1:-1]
        return render_template(open("/templates/wifi_list.html").read(), networks=networks)
    except subprocess.CalledProcessError as e:
        flash(f"nmcli error: {e.stderr}", 'danger')
        return redirect('/')

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

    os.system("sudo systemctl stop hostapd")
    
    try:
        result = subprocess.run(["sudo", "nmcli", "dev", "wifi", "connect", ssid, "password", password], capture_output=True, text=True, check=True)
        flash("Successfully connected!", 'success')
        # Flask sunucusunu kapat
        request.environ.get('werkzeug.server.shutdown')()
    except subprocess.CalledProcessError as e:
        flash(f"Connection error: {e.stderr}", 'danger')
        return redirect('/')

if __name__ == '__main__':
    if not is_connected():
        os.system("sudo systemctl start hostapd")
        run_flask_app()
    check_network()
