import os
import shutil
import subprocess
import logging
import time
import json
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
from config import loadConfig
import pytz

# === Load configuration from SQLite ===
CONFIG_DB = loadConfig()

# === Path Konfigurasi ===
BACKUP_DIR = "/home/pi/logix/database/backup"
STATE_FILE = "/home/pi/logix/database/backup_state.json"

# === Konfigurasi MySQL ===
HOST = CONFIG_DB.get('db_host', '127.0.0.1')
USER = CONFIG_DB.get('db_user', 'logix')
PASSWORD = CONFIG_DB.get('db_password', 'logix')
DATABASE = CONFIG_DB.get('db_name', 'logix')
PORT = CONFIG_DB.get('db_port', '3306')

# Timezone dan koneksi
TIMEZONE = CONFIG_DB.get('timezone', 'Asia/Jakarta')
tz = pytz.timezone(TIMEZONE)
ambilDate = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


# MySQL connection configuration
MYSQL_CONFIG = {
    'host': HOST,
    'user': USER,
    'password': PASSWORD,
    'database': DATABASE,
    'port': PORT
}

# === Setup Logging ===
os.makedirs(BACKUP_DIR, exist_ok=True)

# === Load/Save State ===
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        print(f"[{ambilDate}]Gagal menyimpan state: {e}")

# === Backup Database (MySQL Dump) ===
def backup_database():
    today_str = datetime.today().strftime('%Y-%m-%d')
    sql_filename = f"logix_db_{today_str}.sql"
    sql_path = os.path.join(BACKUP_DIR, sql_filename)
    gz_path = sql_path + ".gz"

    if os.path.exists(gz_path):
        print(f"[{ambilDate}]Backup hari ini sudah ada.")
        return False

    try:
        dump_cmd = [
            "mysqldump",
            "-h", MYSQL_CONFIG["host"],
            "-u", MYSQL_CONFIG["user"],
            f"-p{MYSQL_CONFIG['password']}",
            MYSQL_CONFIG["database"]
        ]
        with open(sql_path, "w") as f:
            subprocess.run(dump_cmd, stdout=f, check=True)

        # Kompres file .sql menjadi .sql.gz
        subprocess.run(["gzip", sql_path], check=True)

        print(f"[{ambilDate}]Backup berhasil dibuat: {gz_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[{ambilDate}]Gagal backup database: {e}")
        return False

# === Hapus Backup Lama (> 30 hari) ===
def cleanup_old_backups():
    cutoff = datetime.today() - timedelta(days=30)
    for fname in os.listdir(BACKUP_DIR):
        if fname.startswith("logix_db_") and fname.endswith(".sql.gz"):
            try:
                date_str = fname.replace("logix_db_", "").replace(".sql.gz", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    os.remove(os.path.join(BACKUP_DIR, fname))
                    print(f"[{ambilDate}]Backup lama dihapus: {fname}")
            except Exception as e:
                print(f"[{ambilDate}]Tidak bisa memproses backup: {fname} => {e}")

# === Optimasi Database (hapus >13 bulan) ===
def optimize_database():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cur = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=396)).strftime('%Y-%m-%d %H:%M:%S')

        cur.execute("DELETE FROM data WHERE date < %s", (cutoff,))
        deleted = cur.rowcount
        print(f"[{ambilDate}]Menghapus {deleted} baris data lebih dari 13 bulan.")

        conn.commit()
        cur.close()
        conn.close()
        print(f"[{ambilDate}]Database dioptimasi (tanpa VACUUM untuk MySQL).")
    except Error as e:
        print(f"[{ambilDate}]Gagal optimasi database: {e}")

# === Main Loop ===
def main_loop():
    print("Memulai background backup mingguan (malam hari)...")
    state = load_state()

    while True:
        now = datetime.now()
        hour = now.hour
        today_str = now.strftime('%Y-%m-%d')

        # Cek apakah sudah seminggu sejak backup terakhir
        last_backup_str = state.get("last_backup", None)
        do_backup = False

        if last_backup_str:
            try:
                last_backup_date = datetime.strptime(last_backup_str, "%Y-%m-%d")
                if now - last_backup_date >= timedelta(days=7):
                    do_backup = True
            except Exception as e:
                print(f"[{ambilDate}]Format last_backup salah: {e}")
                do_backup = True
        else:
            do_backup = True

        # Jalankan hanya malam hari (00:00–01:00)
        if 0 <= hour < 1 and do_backup:
            print(f"[{ambilDate}]Malam hari & waktunya backup mingguan. Menjalankan proses...")
            if backup_database():
                state["last_backup"] = today_str
                save_state(state)
                cleanup_old_backups()
                optimize_database()
        else:
            if not do_backup:
                print(f"[{ambilDate}]Belum waktunya backup mingguan.")
            elif not (0 <= hour < 1):
                print(f"[{ambilDate}]Bukan malam hari. Menunggu waktu 00:00–01:00.")

        time.sleep(3600)  # cek tiap 1 jam

# === Entry Point ===
if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print(f"[{ambilDate}]Dihentikan oleh pengguna.")
    except Exception as e:
        print(f"[{ambilDate}]Fatal error: {e}")
