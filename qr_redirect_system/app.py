from flask import Flask, redirect, request, render_template, url_for
import json
import datetime
import qrcode
import os
import re

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

CONFIG_FILE = os.path.join(BASE_DIR, "redirect.json")
LOG_FILE = os.path.join(BASE_DIR, "scan_log.txt")
QR_FILE = os.path.join(BASE_DIR, "static/qr_code.png")

# In-memory storage for serverless (Vercel doesn't have persistent filesystem)
MEMORY_URL = "https://google.com"
MEMORY_LOGS = []

def get_redirect_url():
    global MEMORY_URL
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return data.get("url", MEMORY_URL)
    except:
        return MEMORY_URL

def set_redirect_url(new_url):
    global MEMORY_URL
    MEMORY_URL = new_url
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"url": new_url}, f)
    except:
        pass

def generate_qr_code():
    """Generate QR code for the /qr endpoint"""
    qr_url = request.host_url + "qr" if request else "https://example.com/qr"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    try:
        os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
        img.save(QR_FILE)
    except:
        pass

def log_scan():
    global MEMORY_LOGS
    log_entry = {
        'timestamp': str(datetime.datetime.now()),
        'ip': request.remote_addr,
        'ua': request.headers.get('User-Agent', 'Unknown')
    }
    MEMORY_LOGS.insert(0, log_entry)
    MEMORY_LOGS = MEMORY_LOGS[:50]  # Keep last 50
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(
                f"{log_entry['timestamp']} | "
                f"IP: {log_entry['ip']} | "
                f"UA: {log_entry['ua']}\n"
            )
    except:
        pass

def get_scan_logs():
    """Parse scan logs and return as list of dicts"""
    global MEMORY_LOGS
    logs = list(MEMORY_LOGS)
    
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        
        for line in reversed(lines[-50:]):
            match = re.match(r'(.+?) \| IP: (.+?) \| UA: (.+)', line.strip())
            if match:
                logs.append({
                    'timestamp': match.group(1),
                    'ip': match.group(2),
                    'ua': match.group(3)
                })
    except FileNotFoundError:
        pass
    return logs[:50]

def get_scan_count():
    """Get total number of scans"""
    count = len(MEMORY_LOGS)
    try:
        with open(LOG_FILE, "r") as f:
            count += len(f.readlines())
    except FileNotFoundError:
        pass
    return count

@app.route("/")
def dashboard():
    """Main dashboard page"""
    try:
        if not os.path.exists(QR_FILE):
            generate_qr_code()
    except:
        pass
    
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

# Vercel handler
app = app

if __name__ == "__main__":
    generate_qr_code()
    app.run(host="0.0.0.0", port=5000, debug=True)
