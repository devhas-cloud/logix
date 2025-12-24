import time
import os
import json
import pytz
import jwt  # Pastikan ini adalah PyJWT
import requests
import mysql.connector
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables
env_path = "/opt/logix/config/env"
if not load_dotenv(dotenv_path=env_path):
    print(f"Error: env file not found at {env_path}")
    exit(1)

# Config from env
STATUS = os.getenv("HAS_STATUS")
HOST = os.getenv('DB_HOST')
USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')
DATABASE = os.getenv('DB_NAME')
PORT = int(os.getenv('DB_PORT'))
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Jakarta')
API_ENDPOINT = os.getenv('HAS_API_URL')
TOKEN_API = os.getenv('HAS_TOKEN_API')
FIELDS = os.getenv('HAS_FIELDS').split(',') if os.getenv('HAS_FIELDS') else []
DEVICE_ID = os.getenv('DEVICE_ID')

# Validasi TOKEN_API
if not TOKEN_API:
    print("Error: HAS_TOKEN_API tidak diset di file env")
    exit(1)

# Validasi FIELDS
if not FIELDS or len(FIELDS) == 0:
    print("Error: HAS_FIELDS tidak diset atau kosong di file env")
    exit(1)
FIELDS = [field.strip() for field in FIELDS if field.strip()]  # Clean whitespace

tz = pytz.timezone(TIMEZONE)

MYSQL_CONFIG = {
    'host': HOST,
    'user': USER,
    'password': PASSWORD,
    'database': DATABASE,
    'port': PORT
}


def write_log(message):
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def ambil_data(FIELDS,DATE):
    try:
        with mysql.connector.connect(**MYSQL_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT {', '.join(FIELDS)} FROM data WHERE has = '0' AND DATE_FORMAT(FROM_UNIXTIME(datetime), '%Y-%m-%d %H:%i') <= '{DATE}'")
                rows = cursor.fetchall()
                
                if rows:
                    return rows
                else:
                    return None
                
    except mysql.connector.Error as e:
        print(f"❌ DB Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error ambil_data: {e}")
        return None



def ambil_tmp(FIELDS,DATE):
    try:
        with mysql.connector.connect(**MYSQL_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT {', '.join(FIELDS)} FROM tmp WHERE has = '0' AND DATE_FORMAT(FROM_UNIXTIME(datetime), '%Y-%m-%d %H:%i') <= '{DATE}'")
                rows = cursor.fetchall()
                
                if rows:
                    return rows
                else:
                    return None
                
    except mysql.connector.Error as e:
        print(f"❌ DB Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error ambil_tmp: {e}")
        return None


def proses_data(rows):
# Contoh output yang diharapkan:[
#     {
#       "recorded_at": "2024-12-14T10:30:00Z",
#       "timestamp": 1702548600,
#       "parameter_name": "temperature",
#       "value": 25.5
#     },
#     {
#       "recorded_at": "2024-12-14T10:30:00Z",
#       "timestamp": 1702548600,
#       "parameter_name": "humidity",
#       "value": 65.2
#     }
#   ]
# 
    data_list = []
    if not rows:
        return data_list
    
    for row in rows:
        recorded_at = None
        timestamp = None
        
        # First pass: extract datetime
        for idx, field in enumerate(FIELDS):
            field = field.strip()
            if field == 'datetime':
                timestamp = row[idx]
                recorded_at = datetime.fromtimestamp(timestamp, tz).isoformat()
                break
        
        # Second pass: create records for each parameter
        for idx, field in enumerate(FIELDS):
            field = field.strip()
            if field != 'datetime':
                record = {
                    'recorded_at': recorded_at,
                    'timestamp': timestamp,
                    'parameter_name': field,
                    'value': row[idx]
                }
                data_list.append(record)
    
    return data_list

def send_data_to_api(FIELDS,DATE):
    #kirim menggunakan token api
    date = DATE.strftime("%Y-%m-%d %H:%M")
    token = TOKEN_API
    field = FIELDS

    
    headers = {
        "X-API-Key": token,
        "Content-Type": "application/json"
    }
    
    # Ambil dan proses data
    data_rows = ambil_data(field, date)
    payloadData = proses_data(data_rows) if data_rows else []
    
    tmp_rows = ambil_tmp(field, date)
    payloadTmp = proses_data(tmp_rows) if tmp_rows else []
    
    #gabungkan data dari data dan tmp
    payload = {
        "device_id": DEVICE_ID,
        "data": payloadData + payloadTmp
    }

    if not payload["data"]:
        print(f"ℹ️ Tidak ada data baru untuk dikirim ke HAS API pada tanggal {date}.")
        return False

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload)
        print("payload:", json.dumps(payload, indent=4, sort_keys=False))

        if response.status_code in [200, 201]:  # 200 OK atau 201 Created
            print(f"✅ Data untuk tanggal {date} berhasil dikirim ke HAS API.")
            #update status has di database
            try:
                with mysql.connector.connect(**MYSQL_CONFIG) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(f"UPDATE data SET has = '1' WHERE DATE_FORMAT(FROM_UNIXTIME(datetime), '%Y-%m-%d %H:%i') <= '{date}'")
                        data_updated = cursor.rowcount
                        cursor.execute(f"UPDATE tmp SET has = '1' WHERE DATE_FORMAT(FROM_UNIXTIME(datetime), '%Y-%m-%d %H:%i') <= '{date}'")
                        tmp_updated = cursor.rowcount
                        conn.commit()
                        print(f"✅ Status 'has' diperbarui: {data_updated} rows di 'data', {tmp_updated} rows di 'tmp' untuk tanggal {date}")
            except mysql.connector.Error as e:
                print(f"❌ DB Error saat memperbarui status 'has': {e}")
            except Exception as e:
                print(f"❌ Error saat memperbarui status 'has': {e}")
            return True
        else:
            print(f"❌ Gagal mengirim data untuk tanggal {date}. Status Code: {response.status_code}, Response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ Error saat mengirim data ke HAS API: {e}")
        return False



def scheduler():
    print("⏱️ Service aktif. Menunggu jadwal pengiriman data ke HAS API...")
    last_run = None
    try:
        while True:
           #kirim 1 menit 1 kali
            now = datetime.now(tz)
            if last_run is None or (now - last_run).total_seconds() >= 60:
                DATE = now.replace(second=0, microsecond=0)
                send_data_to_api(FIELDS,DATE)
                last_run = now
            time.sleep(5)
    except KeyboardInterrupt:
        print("🛑 Service dihentikan manual.")

if __name__ == "__main__":
    if STATUS == "active":
        scheduler()
    else:
        print("Service HAS tidak aktif. Ubah HAS_STATUS di file env menjadi 'active' untuk mengaktifkan.")
   