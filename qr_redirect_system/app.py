from flask import Flask, redirect, request, render_template, url_for
import json
import datetime
import qrcode
import os
import re

app = Flask(__name__)

CONFIG_FILE = "redirect.json"
LOG_FILE = "scan_log.txt"
QR_FILE = "static/qr_code.png"

def get_redirect_url():
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return data.get("url", "https://example.com")
    except:
        return "https://example.com"

def set_redirect_url(new_url):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"url": new_url}, f)
    generate_qr_code()

def generate_qr_code():
    """Generate QR code for the /qr endpoint"""
    # Get the base URL - in production this would be your domain
    qr_url = "http://localhost:5000/qr"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    os.makedirs("static", exist_ok=True)
    img.save(QR_FILE)

def log_scan():
    with open(LOG_FILE, "a") as f:
        f.write(
            f"{datetime.datetime.now()} | "
            f"IP: {request.remote_addr} | "
            f"UA: {request.headers.get('User-Agent')}\n"
        )

def get_scan_logs():
    """Parse scan logs and return as list of dicts"""
    logs = []
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        
        for line in reversed(lines[-50:]):  # Get last 50 logs, newest first
            # Parse: 2024-01-01 12:00:00.123456 | IP: 127.0.0.1 | UA: Mozilla...
            match = re.match(r'(.+?) \| IP: (.+?) \| UA: (.+)', line.strip())
            if match:
                logs.append({
                    'timestamp': match.group(1),
                    'ip': match.group(2),
                    'ua': match.group(3)
                })
    except FileNotFoundError:
        pass
    return logs

def get_scan_count():
    """Get total number of scans"""
    try:
        with open(LOG_FILE, "r") as f:
            return len(f.readlines())
    except FileNotFoundError:
        return 0

@app.route("/")
def dashboard():
    """Main dashboard page"""
    # Ensure QR code exists
    if not os.path.exists(QR_FILE):
        generate_qr_code()
    
    return render_template(
        "index.html",
        current_url=get_redirect_url(),
        logs=get_scan_logs(),
        scan_count=get_scan_count(),
        timestamp=datetime.datetime.now().timestamp(),
        message=request.args.get('message')
    )

@app.route("/update-url", methods=["POST"])
def update_url():
    """Update the redirect URL"""
    new_url = request.form.get("new_url")
    if new_url:
        set_redirect_url(new_url)
        return redirect(url_for('dashboard', message='URL updated successfully!'))
    return redirect(url_for('dashboard'))

@app.route("/qr")
def qr_redirect():
    log_scan()
    destination = get_redirect_url()
    return redirect(destination, code=302)

@app.route("/api/stats")
def api_stats():
    """API endpoint for stats"""
    return {
        "scan_count": get_scan_count(),
        "current_url": get_redirect_url(),
        "recent_logs": get_scan_logs()[:10]
    }

if __name__ == "__main__":
    # Generate QR code on startup
    generate_qr_code()
    app.run(host="0.0.0.0", port=5000, debug=True)
