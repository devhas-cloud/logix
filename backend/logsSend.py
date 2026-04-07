import os
import requests
import pytz
from datetime import datetime
from config import loadConfig

# ======================================================
# Load configuration from SQLite
# ======================================================
CONFIG_DB = loadConfig()

# ======================================================
# Configuration
# ======================================================
API_ENDPOINT = CONFIG_DB.get("has_logs_api_url")
API_TOKEN = CONFIG_DB.get("has_logs_token_api", "")
DEVICE_ID = CONFIG_DB.get("device_id")
TIMEZONE = CONFIG_DB.get("timezone", "Asia/Jakarta")

if not API_ENDPOINT or not DEVICE_ID:
    raise EnvironmentError("Konfigurasi env belum lengkap")

TZ = pytz.timezone(TIMEZONE)

# ======================================================
# HTTP Session
# ======================================================
session = requests.Session()
session.headers.update({
    "X-API-Key": API_TOKEN,
    "Content-Type": "application/json"
})


# ======================================================
# Helper Functions
# ======================================================
def now():
    """Waktu sekarang sesuai timezone."""
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")


def send_log(category: str, message: str, action: str = "unaction") -> bool:
    """
    Kirim log ke server API

    :param category: network | connection | sensor
    :param message: pesan log
    :param action: default unaction
    :return: bool
    """
    payload = {
        "device_id": DEVICE_ID,
        "category": category,
        "message": message,
        "action": action
    }

    try:
        response = session.post(API_ENDPOINT, json=payload, timeout=10)
        response.raise_for_status()

        print(f"[{now()}] Log '{category}' berhasil dikirim")
        return True

    except requests.exceptions.RequestException as e:
        print(f"[{now()}] Gagal mengirim log '{category}': {e}")
        return False


# ======================================================
# Public API (Wrapper)
# ======================================================
def send_network_log(message: str) -> bool:
    return send_log("network", message)


def send_connection_log(message: str) -> bool:
    return send_log("connection", message)


def send_sensor_log(message: str) -> bool:
    return send_log("sensor", message)
