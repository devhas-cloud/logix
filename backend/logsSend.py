import os
import requests
import pytz
from datetime import datetime
from dotenv import load_dotenv

# ======================================================
# Load environment variables
# ======================================================
ENV_PATH = "/home/pi/logix/config/.env"

if not load_dotenv(dotenv_path=ENV_PATH):
    raise FileNotFoundError(f"Env file tidak ditemukan: {ENV_PATH}")

# ======================================================
# Configuration
# ======================================================
API_ENDPOINT = os.getenv("HAS_LOGS_API_URL")
API_TOKEN = os.getenv("HAS_LOGS_TOKEN_API")
DEVICE_ID = os.getenv("DEVICE_ID")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Jakarta")

if not all([API_ENDPOINT, API_TOKEN, DEVICE_ID]):
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
