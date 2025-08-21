import os
import logging
import datetime
from flask import Flask, request, jsonify, abort
import os, requests
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from utils.boto3_utils import SSM

from controllers.kbase_chklist_controller import KbaseChkListController


# ---------------------------
# Load Environment Variables
# ---------------------------
load_dotenv()  # Load .env file

SSM.load_secrets()

APP_PORT = int(os.getenv("APP_PORT", 5000))
LOG_FILE = os.getenv("LOG_FILE", "app.log")
CRON_MINUTE = os.getenv("CRON_MINUTE", "*")  # default: run every minute


# ---------------------------
# Flask App
# ---------------------------
app = Flask(__name__)




# ---------------------------
# Setup Logging (File + Stdout)
# ---------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")

# File Handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Stdout Handler
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)






# ---------------------------
# Scheduled Job
# ---------------------------
def scheduled_task():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Scheduled task executed at {now}")

# ---------------------------
# Scheduler Setup
# ---------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_task, 'cron', minute=CRON_MINUTE)
scheduler.start()



# ---------------------------
# Initialize Controller
# ---------------------------
kbase_controller = KbaseChkListController()



# ---------------------------
# Routes
# ---------------------------
@app.route('/')
def home():
    logger.info("Home route accessed")
    return "AI-Powered Knowledge Base Overhaul Tool flask app"

@app.route('/status')
def status():
    jobs = [str(job) for job in scheduler.get_jobs()]
    logger.info("Status route accessed, returning job list")
    return jsonify({
        "scheduler_running": scheduler.running,
        "jobs": jobs
    })

# Environment config (set these before running)
SITE   = "https://cloudinary.atlassian.net/wiki"  # <-- keep /wiki
EMAIL  = "thomas.gurung@cloudinary.com"
TOKEN  = ""

@app.post("/update/<page_id>")
def update_page(page_id):
    data = request.get_json(silent=True) or {}
    html = data.get("html")
    if not (SITE and EMAIL and TOKEN and html):
        abort(400, "Need CONFLUENCE_SITE/EMAIL/TOKEN env vars and JSON body with 'html'.")

    # 1) Get current title & version
    g = requests.get(f"{SITE}/api/v2/pages/{page_id}",
                     params={"body-format": "storage"},
                     auth=(EMAIL, TOKEN))
    g.raise_for_status()
    p = g.json()
    title = p["title"]
    ver   = p["version"]["number"]

    # 2) Update with new HTML (storage format) and incremented version
    payload = {
        "id": str(page_id),
        "status": "current",
        "title": title,
        "body": {"representation": "storage", "value": html},
        "version": {"number": ver + 1, "message": "update via Flask"}
    }
    u = requests.put(f"{SITE}/api/v2/pages/{page_id}",
                     json=payload, auth=(EMAIL, TOKEN))
    u.raise_for_status()
    return jsonify({"id": page_id, "version": u.json().get("version", {}).get("number")})


# ---------------------------
@app.route('/kbase/process', methods=['GET'])
def process_openai():
    """Calls the KbaseChkListController method"""
    result = kbase_controller.process_openai_request()
    return jsonify(result)


# ---------------------------
@app.route('/zendesk/ticket', methods=['GET'])
def process_zendesk():
    """Calls the KbaseChkListController method"""
    result = kbase_controller.process_zendesk_request()
    return jsonify(result)










# ---------------------------
# Main App
# ---------------------------
if __name__ == '__main__':
    try:
        logger.info(f"Starting Flask app on port {APP_PORT}...")
        app.run(debug=True, use_reloader=False, port=APP_PORT)
    except (KeyboardInterrupt, SystemExit):
        logger.warning("Shutting down scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler stopped")
