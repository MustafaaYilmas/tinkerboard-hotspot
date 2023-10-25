from flask import Flask, render_template, request, redirect, flash
import os
import subprocess

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

@app.route('/')
def index():
    try:
        result = subprocess.run(["sudo", "nmcli", "device", "wifi", "list"], capture_output=True, text=True)
        networks = result.stdout.split('\n')[1:-1]  
        
        if result.stderr:
            flash(f"nmcli error: {result.stderr}", 'danger')
        
        return render_template(open("/templates/wifi_list.html").read(), networks=networks)
    except Exception as e:
        flash(f"Error: {e}", 'danger')
        return redirect('/')

@app.route('/connect', methods=['POST'])
def connect():
    ssid = request.form['ssid']
    password = request.form['password']

    os.system("sudo systemctl stop hostapd")

    result = subprocess.run(["sudo", "nmcli", "dev", "wifi", "connect", ssid, "password", password], capture_output=True, text=True)

    if result.stderr:
        flash(f"Connection error: {result.stderr}", 'danger')
    else:
        flash("Successfully connected!", 'success')

    if not result.stderr:
        os._exit(0) 

    return redirect('/')

if __name__ == '__main__':
    os.system("sudo systemctl start hostapd")
    app.run(host='0.0.0.0', port=5000)
