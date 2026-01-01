from flask import Flask, redirect, request
import json
import datetime

app = Flask(__name__)

CONFIG_FILE = "redirect.json"
LOG_FILE = "scan_log.txt"

def get_redirect_url():
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
    return data.get("url", "https://example.com")

def log_scan():
    with open(LOG_FILE, "a") as f:
        f.write(
            f"{datetime.datetime.now()} | "
            f"IP: {request.remote_addr} | "
            f"UA: {request.headers.get('User-Agent')}\n"
        )

@app.route("/qr")
def qr_redirect():
    log_scan()
    destination = get_redirect_url()
    return redirect(destination, code=302)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
