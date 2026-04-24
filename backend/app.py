from flask import Flask, send_from_directory, jsonify, request, send_file, session
from functools import wraps
import polars as pl
from datetime import datetime, timedelta
import json
import os
import io
import sys
import logging
import traceback
import re
import subprocess
import mysql.connector
import sqlite3
import hashlib
import secrets
from config import loadConfig, mysqlConfig, ambilDateAll, CONFIG_DB_PATH, cekTable

# === Load Configuration from SQLite ===
try:
    CONFIG_DB = loadConfig()
    print("Configuration loaded from SQLite database")
except Exception as e:
    print(f"Failed to load config from SQLite: {e}")
    exit(1)

# === MySQL Config from SQLite ===
DB_CONFIG = mysqlConfig()

# === App Port from SQLite ===
PORT_NUMBER_APP = int(CONFIG_DB.get('port_number_app', '5010'))

# === Path Setup ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend")

# === Load Web Configuration from SQLite ===
try:
    # Parse PARAMETERS from config, filter empty strings
    params_str = CONFIG_DB.get("parameters", "")
    params_list = [p.strip() for p in params_str.split(",") if p.strip()]
    
    CONFIG = {
        "parameters": params_list,
        "satuanph": CONFIG_DB.get("satuan_ph", "pH"),
        "satuanorp": CONFIG_DB.get("satuan_orp", "mV"),
        "satuantds": CONFIG_DB.get("satuan_tds", "mg/L"),
        "satuanconduct": CONFIG_DB.get("satuan_conduct", "µS/cm"),
        "satuando": CONFIG_DB.get("satuan_do", "mg/L"),
        "satuansalinity": CONFIG_DB.get("satuan_salinity", "ppt"),
        "satuannh3n": CONFIG_DB.get("satuan_nh3n", "mg/L"),
        "satuanturb": CONFIG_DB.get("satuan_turb", "NTU"),
        "satuantss": CONFIG_DB.get("satuan_tss", "mg/L"),
        "satuancod": CONFIG_DB.get("satuan_cod", "mg/L"),
        "satuanbod": CONFIG_DB.get("satuan_bod", "mg/L"),
        "satuanno3": CONFIG_DB.get("satuan_no3", "mg/L"),
        "satuanatemp": CONFIG_DB.get("satuan_atemp", "°C"),
        "satuanwtemp": CONFIG_DB.get("satuan_wtemp", "°C"),
        "satuanapress": CONFIG_DB.get("satuan_apress", "mbar"),
        "satuanwpress": CONFIG_DB.get("satuan_wpress", "mbar"),
        "satuanbattery": CONFIG_DB.get("satuan_battery", "V"),
        "satuandepth": CONFIG_DB.get("satuan_depth", "m"),
        "satuanflow": CONFIG_DB.get("satuan_flow", "L/s"),
        "satuantflow": CONFIG_DB.get("satuan_tflow", "L/s"),
        "satuanhum": CONFIG_DB.get("satuan_hum", "%"),
        "satuanwspeed": CONFIG_DB.get("satuan_wspeed", "m/s"),
        "satuanwdir": CONFIG_DB.get("satuan_wdir", "°"),
        "satuanrain": CONFIG_DB.get("satuan_rain", "mm"),
        "satuansrad": CONFIG_DB.get("satuan_srad", "W/m²"),
        "device": CONFIG_DB.get("device_id", ""),
        "location": CONFIG_DB.get("location_name", ""),
        "software": CONFIG_DB.get("software_version", ""),
        "titlename": CONFIG_DB.get("web_title", ""),
        "headername": CONFIG_DB.get("web_name", ""),
        "gapweb": int(CONFIG_DB.get("gap_web", "3")),
        "geo": {
            "latitude": float(CONFIG_DB.get("geo_latitude", "0")),
            "longitude": float(CONFIG_DB.get("geo_longitude", "0")),
        }
    }
    print("Web CONFIG loaded from SQLite")
except Exception as e:
    print(f"Failed to load web config from SQLite: {e}")
    CONFIG = {"parameters": []}
    

# === Initialize Database Tables ===
try:
    cekTable()
    print("Database tables initialized")
except Exception as e:
    print(f"Warning during table initialization: {e}")

# === Flask App ===
app = Flask(__name__, static_folder=None)

# === Authentication Setup ===
app.secret_key = secrets.token_hex(32)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

# Default credentials - change these in production
# (Credentials are now managed via SQLite config)

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash

def login_required(f):
    """Decorator to require login for protected endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized', 'message': 'Please login first'}), 401
        return f(*args, **kwargs)
    return decorated_function

# === USB Mount Management ===
BASE_MOUNT_DIR = "/mnt"
MOUNTED_USB = []


def query_to_dataframe(query, params=None):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not rows:
        # Return empty DataFrame with proper structure
        return pl.DataFrame([])
    
    # Convert to Polars with schema inference on more rows
    df = pl.DataFrame(rows, infer_schema_length=None)
    # Polars handles nulls natively for JSON serialization
    return df


def get_usb_devices():
    devices = []
    try:
        result = subprocess.run(['lsblk', '-S', '-o', 'NAME,TRAN,VENDOR'], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()[1:]
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 3:
                name, tran, vendor = parts[:3]
                if tran.lower() == 'usb':
                    part_result = subprocess.run(
                        ['lsblk', '-nrpo', 'NAME,TYPE,MOUNTPOINT', f'/dev/{name}'],
                        capture_output=True, text=True
                    )
                    for part_line in part_result.stdout.strip().splitlines():
                        part_info = part_line.strip().split()
                        if len(part_info) >= 3 and part_info[1] == "part":
                            part_name, _, mount_point = part_info
                            if mount_point == "-" or not mount_point:
                                safe_vendor = vendor.replace(" ", "_")
                                mount_point = os.path.join(BASE_MOUNT_DIR, safe_vendor)
                                os.makedirs(mount_point, exist_ok=True)
                                try:
                                    subprocess.run(['mount', part_name, mount_point], check=True)
                                    print(f"Mounted {part_name} at {mount_point}")
                                    MOUNTED_USB.append(mount_point)
                                except subprocess.CalledProcessError as e:
                                    print(f"Mount failed for {part_name}: {e}")
                                    continue
                            devices.append({"label": vendor.strip(), "mount": mount_point})
        return devices
    except Exception as e:
        print(f"USB detection error: {e}")
        return []


def cleanup_usb_mounts():
    global MOUNTED_USB
    for mount_point in MOUNTED_USB:
        try:
            subprocess.run(['umount', mount_point], check=True)
            print(f"Unmounted {mount_point}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to unmount {mount_point}: {e}")
    MOUNTED_USB = []


def sanitize_filename(filename):
    filename = filename.replace(":", "-").replace("/", "-")
    return re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename)


# === Publik API Endpoints ===



@app.route("/")
def index():
    """Root URL - serves public home page"""
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route('/api/config')
def get_config():
    return jsonify(CONFIG)

@app.route('/api/latest')
def latest_data():
    try:
        params = CONFIG.get("parameters", [])
        if not params:
            return jsonify({"error": "No parameters defined in config"}), 400

        param_fields = ', '.join(params + ["date"])
        query = f"""
                    SELECT {param_fields}
                    FROM (
                        SELECT {param_fields} FROM data
                        UNION ALL
                        SELECT {param_fields} FROM tmp
                    ) AS combined
                    ORDER BY date DESC LIMIT 1
                """
        df = query_to_dataframe(query)

        if df.is_empty():
            return jsonify({param: None for param in params})

        row = df.row(0, named=True)
        if 'date' in row and row['date']:
            row['date_str'] = row['date'].strftime("%Y-%m-%d %H:%M")
        return jsonify(row)

    except Exception as e:
        print(f"Exception in /api/latest: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/history')
def history_data():
    param = request.args.get('param', 'temp')
    range_time = request.args.get('range', 'realtime')
    now = datetime.now()
    start_time = {
        "realtime": now - timedelta(minutes=15),
        "1h": now - timedelta(hours=1),
        "12h": now - timedelta(hours=12),
        "1d": now - timedelta(days=1),
        "3d": now - timedelta(days=3),
        "7d": now - timedelta(days=7)
    }.get(range_time, now - timedelta(minutes=15))

    try:
        query = f"""
            SELECT date, {param}
            FROM (
                SELECT date, {param} FROM data
                UNION ALL
                SELECT date, {param} FROM tmp
            ) AS combined
            WHERE date >= %s
            ORDER BY date ASC;
        """
        df = query_to_dataframe(query, (start_time,))

        if param not in df.columns:
            return jsonify({"timestamps": [], "values": []})

        return jsonify({
            "timestamps": df["date"].cast(pl.Utf8).to_list(),
            "values": df[param].to_list()
        })
    except Exception as e:
        print(f"/api/history error: {e}")
        return jsonify({"timestamps": [], "values": [], "error": str(e)}), 500


@app.route('/api/windrose')
def windrose_data():
    range_time = request.args.get('range', 'realtime')
    now = datetime.now()
    start_time = {
        "realtime": now - timedelta(minutes=15),
        "1h": now - timedelta(hours=1),
        "12h": now - timedelta(hours=12),
        "1d": now - timedelta(days=1),
        "3d": now - timedelta(days=3),
        "7d": now - timedelta(days=7)
    }.get(range_time, now - timedelta(minutes=15))

    try:
        
        query = f"""
            SELECT date, wspeed, wdir
            FROM (
                SELECT date,  wspeed, wdir FROM data
                UNION ALL
                SELECT date,  wspeed, wdir FROM tmp
            ) AS combined
            WHERE date >= %s
            ORDER BY date ASC;
        """
        df = query_to_dataframe(query, (start_time,))

        if "wspeed" not in df.columns or "wdir" not in df.columns:
            return jsonify({"timestamps": [], "wspeed": [], "wdir": []})

        return jsonify({
            "timestamps": df["date"].cast(pl.Utf8).to_list(),
            "wspeed": df["wspeed"].to_list(),
            "wdir": df["wdir"].to_list()
        })

    except Exception as e:
        print(f"/api/windrose error: {e}")
        traceback.print_exc()
        return jsonify({"timestamps": [], "wspeed": [], "wdir": [], "error": str(e)}), 500



@app.route('/api/usb-list')
def list_usb_devices():
    try:
        usb_devices = get_usb_devices()
        devices = ["download"] + [usb["label"] for usb in usb_devices]
        return jsonify(devices)
    except Exception as e:
        print(f"USB list error: {e}")
        return jsonify(["download"]), 500
    finally:
        cleanup_usb_mounts()


@app.route('/api/export', methods=['POST'])
def export_data():
    try:
        data = request.get_json()
        start = data.get("start")
        end = data.get("end")
        destination = data.get("destination", "download")

        if not start or not end:
            return jsonify({"error": "Parameter 'start' dan 'end' wajib diisi."}), 400

        print(f"Export request: {start} → {end} to {destination}")
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        
        # Export sesuai parameter yang dipilih dari CONFIG
        # Pastikan 'device', 'date' selalu disertakan
        parameters = CONFIG.get("parameters", [])
        
        # Filter empty strings jika ada
        parameters = [p for p in parameters if p]
        
        selected_params = ["device", "date"] + parameters
        param_fields = ', '.join(selected_params)
        query = f"""
            SELECT {param_fields} FROM (
                SELECT {param_fields} FROM data
                UNION ALL
                SELECT {param_fields} FROM tmp
            ) AS combined
            WHERE date BETWEEN %s AND %s ORDER BY date ASC;
        """
        df = query_to_dataframe(query, (start_dt, end_dt))
       
        
        if df.is_empty():
            return jsonify({"error": "Tidak ada data dalam rentang waktu tersebut."}), 400

        # Tambahkan nomor urut
        df = df.with_row_count(name="no", offset=1)
        filename = sanitize_filename(f"export_{start}_{end}.csv")
       

        if destination == "download":
            # Polars write_csv returns string directly, not bytes
            csv_string = df.write_csv()
            mem = io.BytesIO()
            mem.write(csv_string.encode('utf-8'))
            mem.seek(0)
            return send_file(
                mem,
                download_name=filename,
                as_attachment=True,
                mimetype='text/csv'
            )
        else:
            usb_devices = get_usb_devices()
            mount_point = next((usb["mount"] for usb in usb_devices if usb["label"] == destination), None)
            if not mount_point or not os.access(mount_point, os.W_OK):
                return jsonify({"error": f"USB '{destination}' tidak ditemukan atau tidak bisa ditulis."}), 500
            export_path = os.path.join(mount_point, filename)
            df.write_csv(export_path)
            print(f"Data exported to: {export_path}")
            return jsonify({"status": "success", "path": export_path})
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cleanup_usb_mounts()


@app.route('/api/wifi-status')
def wifi_status():
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        ssid_connected = "-"
        for line in lines:
            if line.startswith("yes:"):
                parts = line.split(":")
                if len(parts) > 1:
                    ssid_connected = parts[1]
                break
        # IP address
        ip_address = "-"
        try:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            ip_address = result.stdout.strip().split()[0] if result.stdout.strip() else "-"
        except Exception as e:
            print(f"IP address retrieval error: {e}")


        ping_check = subprocess.run(['ping', '-c', '1', '8.8.8.8'], stdout=subprocess.DEVNULL)
        connected = ping_check.returncode == 0

        return jsonify({'connected': connected, 'ssid': ssid_connected, 'ip': ip_address})
    except Exception as e:
        print(f"WiFi status error: {e}")
        return jsonify({'connected': False, 'ssid': '-', 'ip': '-'})



@app.route('/api/wifi-scan')
def wifi_scan():
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'ssid', 'dev', 'wifi'], capture_output=True, text=True)
        ssids = list({s for s in result.stdout.strip().split('\n') if s.strip()})
        return jsonify({'ssids': ssids})
    except Exception as e:
        print(f"WiFi scan error: {e}")
        return jsonify({'ssids': []})


@app.route('/api/connect-wifi', methods=['POST'])
def connect_wifi():
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password')
        #print(f"Simulating connect to SSID: {ssid}")
        subprocess.run(['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password])
        return jsonify({'message': f'Terhubung ke {ssid} .'})
    except Exception as e:
        print(f"Connect WiFi error: {e}")
        return jsonify({'message': 'Gagal menghubungkan ke WiFi.'}), 500


@app.route('/api/system/restart', methods=['POST'])
def restart():
    logging.warning("Restart requested!")
    os.system('sudo reboot')
    return jsonify({
        "success": True,
        "message": "System restart initiated. Please wait..."
    }), 200


@app.route('/api/system/shutdown', methods=['POST'])
def shutdown():
    logging.warning("Shutdown requested!")
    os.system('sudo shutdown now')
    return '', 204



# === Authentication Endpoints ===============

@app.route("/login")
def login_page():
    """Login page - for admin authentication"""
    return send_from_directory(FRONTEND_DIR, "login.html")


@app.route("/admin")
def admin():
    """Admin dashboard - requires authentication"""
    return send_from_directory(FRONTEND_DIR, "admin.html")


@app.route("/admin/<path:filepath>")
def serve_admin_assets(filepath):
    """Serve static assets for admin dashboard (components, sections, css, js)"""
    return send_from_directory(FRONTEND_DIR, filepath)


@app.route("/<path:filepath>")
def serve_frontend(filepath):
    """Serve public frontend assets (css, js, images, etc)"""
    return send_from_directory(FRONTEND_DIR, filepath)


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint for configuration management"""
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        # Check credentials
        current_config = loadConfig()
        expected_user = current_config.get('web_username', 'admin')
        expected_pass = current_config.get('web_password', 'has123456')
        
        # Verify
        if username == expected_user and password == expected_pass:
            session['username'] = username
            session.permanent = True
            print(f"User '{username}' logged in successfully")
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            logging.warning(f"Failed login attempt for user '{username}'")
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    try:
        username = session.get('username', 'unknown')
        session.clear()
        print(f"User '{username}' logged out")
        return jsonify({'success': True, 'message': 'Logout successful'})
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/auth/status')
def auth_status():
    """Check current authentication status"""
    if 'username' in session:
        return jsonify({'authenticated': True, 'username': session['username']})
    return jsonify({'authenticated': False})





# ==================== MONITORING ENDPOINTS ====================
@app.route('/api/configuration', methods=['GET', 'POST'])
def get_configuration():
    """Get or Save configuration"""
    # Handle GET request - Return full configuration from database
    if request.method == 'GET':
        try:
            conn = sqlite3.connect(CONFIG_DB_PATH)
            cursor = conn.cursor()
            
            # Read from config table
            cursor.execute("SELECT * FROM config WHERE id=1")
            row = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            config_dict = dict(zip(columns, row)) if row else {}
            
            # Read from satuan table
            cursor.execute("SELECT * FROM satuan WHERE id=1")
            row_satuan = cursor.fetchone()
            columns_satuan = [desc[0] for desc in cursor.description]
            satuan_dict = dict(zip(columns_satuan, row_satuan)) if row_satuan else {}
            
            # Merge both dictionaries
            config_dict.update(satuan_dict)
            
            cursor.close()
            conn.close()
            
            return jsonify(config_dict)
        except Exception as e:
            print(f"Error reading configuration: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    # Handle POST request - Save configuration to database
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"success": False, "message": "No data provided"}), 400
            
            conn = sqlite3.connect(CONFIG_DB_PATH)
            cursor = conn.cursor()
            
            # Define all config fields (from config table)
            config_fields = {
                'port_number_app', 'port_number_log', 'timezone',
                'db_host', 'db_port', 'db_name', 'db_user', 'db_password',
                'at500_status', 'at500_port', 'rt200_status', 'rt200_port',
                'sem5096_status', 'sem5096_port', 'mace_status', 'mace_port',
                'iscan_status', 'iscan_port', 'ltnc_status', 'ltnc_port',
                'spectro_status', 'spectro_ip', 'spectro_port',
                'contlyte_status', 'contlyte_port', 'ds502_status', 'ds502_port',
                'ammonia200_status', 'ammonia200_port', 'cod200x_status', 'cod200x_port',
                'h1601_status', 'h1601_port', 'ph200_status', 'ph200_port',
                'tss200x_status', 'tss200x_port', 'xymd02_status', 'xymd02_port', 'xymd02_slave_id',
                'delay',
                'klhk_status', 'klhk_api_url', 'klhk_token_url', 'klhk_uid', 'klhk_fields', 'klhk_max_dup_retry', 'klhk_target_minute',
                'has_status', 'has_api_url', 'has_token_api', 'has_fields',
                'has_logs_api_url', 'has_logs_token_api',
                'parameters', 'gap_web', 'web_title', 'web_name',
                'web_username', 'web_password',
                'device_id', 'location_name', 'software_version', 'geo_latitude', 'geo_longitude'
            }
            
            # Define all satuan fields (from satuan table) - use lowercase to match database columns
            satuan_fields = {
                'satuan_ph', 'satuan_cod', 'satuan_tss', 'satuan_nh3n', 'satuan_flow',
                'satuan_atemp', 'satuan_wtemp', 'satuan_orp', 'satuan_turb', 'satuan_tds',
                'satuan_conduct', 'satuan_do', 'satuan_salinity', 'satuan_battery',
                'satuan_depth', 'satuan_tflow', 'satuan_no3', 'satuan_bod',
                'satuan_apress', 'satuan_wpress', 'satuan_hum', 'satuan_wspeed', 'satuan_wdir',
                'satuan_rain', 'satuan_srad'
            }
            
            # Filter data for config table
            config_data = {k: v for k, v in data.items() if k in config_fields}
            if config_data:
                set_clause = ', '.join([f'{k}=?' for k in config_data.keys()])
                query = f"UPDATE config SET {set_clause} WHERE id=1"
                cursor.execute(query, list(config_data.values()))
                print(f"Updated config table: {list(config_data.keys())}")
            
            # Filter data for satuan table
            satuan_data = {k: v for k, v in data.items() if k in satuan_fields}
            if satuan_data:
                set_clause = ', '.join([f'{k}=?' for k in satuan_data.keys()])
                query = f"UPDATE satuan SET {set_clause} WHERE id=1"
                cursor.execute(query, list(satuan_data.values()))
                print(f"Updated satuan table: {list(satuan_data.keys())}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"Configuration saved successfully: {len(data)} fields updated")
            
            # Reload config in memory from database
            global CONFIG_DB, CONFIG
            CONFIG_DB = loadConfig()
            params_str = CONFIG_DB.get("parameters", "")
            params_list = [p.strip() for p in params_str.split(",") if p.strip()]
            CONFIG["parameters"] = params_list
            
            # Update other CONFIG values from database
            CONFIG.update({
                "satuanph": CONFIG_DB.get("satuan_ph", "pH"),
                "satuanorp": CONFIG_DB.get("satuan_orp", "mV"),
                "satuantds": CONFIG_DB.get("satuan_tds", "mg/L"),
                "satuanconduct": CONFIG_DB.get("satuan_conduct", "µS/cm"),
                "satuando": CONFIG_DB.get("satuan_do", "mg/L"),
                "satuansalinity": CONFIG_DB.get("satuan_salinity", "ppt"),
                "satuannh3n": CONFIG_DB.get("satuan_nh3n", "mg/L"),
                "satuanturb": CONFIG_DB.get("satuan_turb", "NTU"),
                "satuantss": CONFIG_DB.get("satuan_tss", "mg/L"),
                "satuancod": CONFIG_DB.get("satuan_cod", "mg/L"),
                "satuanbod": CONFIG_DB.get("satuan_bod", "mg/L"),
                "satuanno3": CONFIG_DB.get("satuan_no3", "mg/L"),
                "satuanatemp": CONFIG_DB.get("satuan_atemp", "°C"),
                "satuanwtemp": CONFIG_DB.get("satuan_wtemp", "°C"),
                "satuanapress": CONFIG_DB.get("satuan_apress", "mbar"),
                "satuanwpress": CONFIG_DB.get("satuan_wpress", "mbar"),
                "satuanbattery": CONFIG_DB.get("satuan_battery", "V"),
                "satuandepth": CONFIG_DB.get("satuan_depth", "m"),
                "satuanflow": CONFIG_DB.get("satuan_flow", "L/s"),
                "satuantflow": CONFIG_DB.get("satuan_tflow", "L/s"),
                "satuanhum": CONFIG_DB.get("satuan_hum", "%"),
                "satuanwspeed": CONFIG_DB.get("satuan_wspeed", "m/s"),
                "satuanwdir": CONFIG_DB.get("satuan_wdir", "°"),
                "satuanrain": CONFIG_DB.get("satuan_rain", "mm"),
                "satuansrad": CONFIG_DB.get("satuan_srad", "W/m²"),
                "device": CONFIG_DB.get("device_id", ""),
                "location": CONFIG_DB.get("location_name", ""),
                "software": CONFIG_DB.get("software_version", ""),
                "titlename": CONFIG_DB.get("web_title", ""),
                "headername": CONFIG_DB.get("web_name", ""),
                "gapweb": int(CONFIG_DB.get("gap_web", "3")),
                "geo": {
                    "latitude": float(CONFIG_DB.get("geo_latitude", "0")),
                    "longitude": float(CONFIG_DB.get("geo_longitude", "0")),
                }
            })
            
            return jsonify({
                "success": True,
                "message": "Configuration saved successfully to database",
                "updated_count": len(data),
                "updated_keys": list(data.keys())
            })
        except Exception as e:
            print(f"Error saving configuration: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500



@app.route('/api/data/pending', methods=['GET'])
@login_required
def get_pending_data():
    """Mendapatkan data yang siap dikirim (belum dikirim ke API)"""
    try:
        mysql_config = mysqlConfig()
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        # Get data yang belum dikirim (status != 'sent' atau dateterkirim NULL)
        query = """
        SELECT * FROM tmp 
        WHERE status IS NULL OR status = ''
        ORDER BY `date` DESC 
        LIMIT 1000
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convert datetime objects to strings and handle None values
        for row in rows:
            if isinstance(row.get('date'), datetime):
                row['date'] = row['date'].isoformat()
            if isinstance(row.get('dateterkirim'), datetime):
                row['dateterkirim'] = row['dateterkirim'].isoformat()
            
            # Ensure numeric fields are properly formatted
            for key in ['pH', 'orp', 'tds', 'do', 'conduct', 'flow', 'cod', 'tss', 'bod']:
                if row.get(key) is not None:
                    if isinstance(row[key], (int, float)):
                        row[key] = float(row[key])
        
        # Load config to get klhk_fields
        from config import loadConfig
        config = loadConfig()
        klhk_fields = config.get('klhk_fields', 'datetime,pH,cod,tss,nh3n,flow')
        
        return jsonify({
            'success': True,
            'count': len(rows),
            'data': rows,
            'klhk_fields': klhk_fields
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/api/retry/status', methods=['GET'])
@login_required
def get_retry_status():
    """Get the status of automatic KLHK retry sending"""
    try:
        from config import loadConfig
        config = loadConfig()
        klhk_status = config.get('klhk_status', 'inactive')
        target_minute = config.get('klhk_target_minute', '10')
        
        # Check if retry.py process is running
        import glob
        try:
            is_running = False
            # Scan /proc/*/cmdline to find retry.py process
            for cmdline_file in glob.glob('/proc/[0-9]*/cmdline'):
                try:
                    with open(cmdline_file, 'r') as f:
                        cmdline = f.read().replace('\x00', ' ')
                        # Check if this is "python -u retry.py"
                        if 'python' in cmdline and ' retry.py' in cmdline:
                            is_running = True
                            break
                except (IOError, OSError):
                    continue
        except Exception as e:
            is_running = False
        
        return jsonify({
            'success': True,
            'status': klhk_status,
            'is_running': is_running,
            'target_minute': target_minute,
            'schedule': f'Setiap jam pada menit ke-{target_minute}'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/retry/manual', methods=['POST'])
@login_required
def manual_retry():
    """Trigger manual KLHK retry data sending with optional date range"""
    try:
        from config import loadConfig
        config = loadConfig()
        klhk_status = config.get('klhk_status', 'inactive')
        
        if klhk_status.lower() != 'active':
            return jsonify({
                'success': False,
                'error': 'KLHK retry module is not active. Please enable it in configuration.'
            }), 400
        
        # Extract optional date parameters from request
        request_data = request.get_json(force=True, silent=True) or {}
        date_from = request_data.get('date_from')
        date_to = request_data.get('date_to')
        
        # Check if there's data to retry
        try:
            mysql_config = mysqlConfig()
            conn = mysql.connector.connect(**mysql_config)
            cursor = conn.cursor()
            
            # Build COUNT query based on whether date filters are provided
            if date_from and date_to:
                cursor.execute("SELECT COUNT(*) FROM tmp WHERE status='retry' AND `date` >= %s AND `date` <= %s", (date_from, date_to))
                operation_type = "filtered"
                print(f"[RETRY] Counting filtered data: from {date_from} to {date_to}")
            else:
                cursor.execute("SELECT COUNT(*) FROM tmp WHERE status='retry'")
                operation_type = "all"
                print(f"[RETRY] Counting all retry data")
            
            retry_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            if retry_count == 0:
                return jsonify({
                    'success': False,
                    'error': 'Tidak ada data retry untuk dikirim. Silakan periksa data di tabel.'
                }), 400
        except Exception as db_error:
            # If DB check fails, continue anyway
            retry_count = 0
            print(f"[RETRY] DB check failed: {db_error}")
        
        # Import and run the retry function
        import sys
        sys.path.insert(0, os.path.join(BASE_DIR, '..', 'klhk'))
        
        try:
            from retry import ambil_data, reload_config
            
            # Wrapper function to reload config before running
            def manual_retry_wrapper():
                # Redirect stdout to retry.log
                import sys
                log_file = open(os.path.join(BASE_DIR, '..', 'logs', 'retry.log'), 'a')
                sys.stdout = log_file
                sys.stderr = log_file
                
                try:
                    reload_config()  # Reload config to ensure STATUS is active
                    ambil_data(date_from=date_from, date_to=date_to)
                finally:
                    log_file.flush()
                    log_file.close()
                    sys.stdout = sys.__stdout__
                    sys.stderr = sys.__stderr__
            
            # Run in a thread to avoid blocking
            import threading
            thread = threading.Thread(target=manual_retry_wrapper)
            thread.daemon = True
            thread.start()
            
            print(f"[RETRY] Manual retry triggered - count: {retry_count}, type: {operation_type}")
            return jsonify({
                'success': True,
                'count': retry_count,
                'type': operation_type,
                'message': f'Pengiriman ulang manual berhasil dipicu untuk {retry_count} data. Periksa log untuk detail.'
            }), 200
            
        except Exception as retry_error:
            return jsonify({
                'success': False,
                'error': f'Failed to trigger retry: {str(retry_error)}'
            }), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/api/data/retry', methods=['GET'])
@login_required
def get_retry_data():
    """Mendapatkan data yang statusnya retry (gagal kirim sebelumnya)"""
    try:
        mysql_config = mysqlConfig()
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        # Get data dengan status 'retry'
        query = """
        SELECT * FROM tmp 
        WHERE status = 'retry'
        ORDER BY `date` DESC 
        LIMIT 1000
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convert datetime objects to strings and handle None values
        for row in rows:
            if isinstance(row.get('date'), datetime):
                row['date'] = row['date'].isoformat()
            if isinstance(row.get('dateterkirim'), datetime):
                row['dateterkirim'] = row['dateterkirim'].isoformat()
            
            # Ensure numeric fields are properly formatted
            for key in ['pH', 'orp', 'tds', 'do', 'conduct', 'flow', 'cod', 'tss', 'bod']:
                if row.get(key) is not None:
                    if isinstance(row[key], (int, float)):
                        row[key] = float(row[key])
        
        # Load config to get klhk_fields
        from config import loadConfig
        config = loadConfig()
        klhk_fields = config.get('klhk_fields', 'datetime,pH,cod,tss,nh3n,flow')
        
        return jsonify({
            'success': True,
            'count': len(rows),
            'data': rows,
            'klhk_fields': klhk_fields
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/klhk-success', methods=['GET'])
@login_required
def get_klhk_success():
    """Mendapatkan data pengiriman KLHK yang berhasil"""
    try:
        mysql_config = mysqlConfig()
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        # Get data dari tabel klhk_json_encode_success
        query = """
        SELECT * FROM klhk_json_encode_success WHERE status = 1
        ORDER BY timestamp DESC 
        LIMIT 10
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convert datetime objects to strings
        for row in rows:
            if isinstance(row.get('timestamp'), datetime):
                row['timestamp'] = row['timestamp'].isoformat()
        
        return jsonify({
            'success': True,
            'count': len(rows),
            'data': rows
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data/klhk-logs', methods=['GET'])
@login_required
def get_klhk_logs():
    """Mendapatkan data pengiriman KLHK yang berhasil"""
    try:
        mysql_config = mysqlConfig()
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        # Get data dari tabel klhk_json_encode_success
        query = """
        SELECT * FROM klhk_json_encode_success
        ORDER BY timestamp DESC 
        LIMIT 1000
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convert datetime objects to strings
        for row in rows:
            if isinstance(row.get('timestamp'), datetime):
                row['timestamp'] = row['timestamp'].isoformat()
        
        return jsonify({
            'success': True,
            'count': len(rows),
            'data': rows
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data/stats', methods=['GET'])
@login_required
def get_data_stats():
    """Mendapatkan statistik data pengiriman"""
    try:
        mysql_config = mysqlConfig()
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        # Total data (dari tmp dan data table)
        cursor.execute("SELECT COUNT(*) as total FROM tmp")
        tmp_count = cursor.fetchone()
        total_tmp = tmp_count['total'] if tmp_count else 0
        
        cursor.execute("SELECT COUNT(*) as total FROM data")
        data_count = cursor.fetchone()
        total_data = data_count['total'] if data_count else 0
        
        total = total_tmp + total_data
        
        # Data pending (status NULL atau empty)
        cursor.execute("SELECT COUNT(*) as pending FROM tmp WHERE status IS NULL OR status = ''")
        pending_row = cursor.fetchone()
        pending = pending_row['pending'] if pending_row else 0
        
        # Data retry (status = 'retry')
        cursor.execute("SELECT COUNT(*) as retry FROM tmp WHERE status = 'retry'")
        retry_row = cursor.fetchone()
        retry = retry_row['retry'] if retry_row else 0
        
        # Data sent
        cursor.execute("SELECT COUNT(*) as sent FROM data")
        sent_row = cursor.fetchone()
        sent = sent_row['sent'] if sent_row else 0
        
        # KLHK success
        cursor.execute("SELECT COUNT(*) as klhk_success FROM klhk_json_encode_success WHERE status = 1")
        klhk_row = cursor.fetchone()
        klhk_success = klhk_row['klhk_success'] if klhk_row else 0
        
        # Last sync
        cursor.execute("SELECT MAX(timestamp) as last_sync FROM klhk_json_encode_success WHERE status = 1")
        last_sync_row = cursor.fetchone()
        if last_sync_row and last_sync_row['last_sync']:
            last_sync = last_sync_row['last_sync'].isoformat() if isinstance(last_sync_row['last_sync'], datetime) else str(last_sync_row['last_sync'])
        else:
            last_sync = 'Belum ada data'
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_data': total,
                'pending_data': pending,
                'retry_data': retry,
                'sent_data': sent,
                'klhk_success': klhk_success,
                'last_sync': last_sync
            }
        }), 200
    
    except Exception as e:
        import traceback
        print(f"Error in get_data_stats: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/send/status', methods=['GET'])
@login_required
def get_send_status():
    """Get the status of automatic KLHK sending"""
    try:
        from config import loadConfig
        config = loadConfig()
        klhk_status = config.get('klhk_status', 'inactive')
        target_minute = 0
        
        # Check if send.py process is running
        # Note: pgrep is not available in slim Docker image, use /proc instead
        import glob
        try:
            is_running = False
            # Scan /proc/*/cmdline to find send.py process
            for cmdline_file in glob.glob('/proc/[0-9]*/cmdline'):
                try:
                    with open(cmdline_file, 'r') as f:
                        cmdline = f.read().replace('\x00', ' ')
                        # Check if this is "python -u send.py" (not hasSend.py)
                        if 'python' in cmdline and ' send.py' in cmdline:
                            is_running = True
                            break
                except (IOError, OSError):
                    # Process might have terminated, skip
                    continue
        except Exception as e:
            is_running = False
        
        return jsonify({
            'success': True,
            'status': klhk_status,
            'is_running': is_running,
            'target_minute': target_minute,
            'schedule': f'Setiap jam pada menit ke-{target_minute}'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/send/manual', methods=['POST'])
@login_required
def manual_send():
    """Trigger manual KLHK data sending"""
    try:
        from config import loadConfig
        config = loadConfig()
        klhk_status = config.get('klhk_status', 'inactive')
        
        if klhk_status.lower() != 'active':
            return jsonify({
                'success': False,
                'error': 'KLHK send module is not active. Please enable it in configuration.'
            }), 400
        
        # Extract optional date range from request (handle empty/malformed body)
        try:
            request_data = request.get_json(force=True, silent=True) or {}
        except Exception as json_error:
            print(f"[SEND] JSON parse error: {str(json_error)}, using empty dict")
            request_data = {}
        
        date_from = request_data.get('date_from')
        date_to = request_data.get('date_to')
        
        print(f"[SEND] Manual send triggered. date_from={date_from}, date_to={date_to}")
        
        # Check if there's data to send
        try:
            mysql_config = mysqlConfig()
            conn = mysql.connector.connect(**mysql_config)
            cursor = conn.cursor()
            
            # Count data with optional date range filter
            if date_from and date_to:
                cursor.execute(
                    "SELECT COUNT(*) FROM tmp WHERE (status IS NULL OR status = '') AND `date` >= %s AND `date` <= %s",
                    [date_from, date_to]
                )
                print(f"[SEND] Filtering count with date_from={date_from}, date_to={date_to}")
            else:
                cursor.execute("SELECT COUNT(*) FROM tmp WHERE status IS NULL OR status = ''")
                print(f"[SEND] Counting all pending data (no date filter)")
            
            pending_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            if pending_count == 0:
                error_msg = 'Tidak ada data pending untuk dikirim dalam range tanggal tersebut.' if (date_from and date_to) else 'Tidak ada data pending untuk dikirim. Silakan periksa data di tabel.'
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
            
            print(f"[SEND] Found {pending_count} rows to send")
        except Exception as db_error:
            print(f"[SEND] Database error during count: {str(db_error)}")
            # If DB check fails, continue anyway
            pending_count = 0
        
        # Import and run the send function
        import sys
        sys.path.insert(0, os.path.join(BASE_DIR, '..', 'klhk'))
        
        try:
            from send import ambil_data, update_config
            
            # Wrapper function to update config before running
            def manual_send_wrapper():
                # Redirect stdout to send.log
                import sys
                log_file = open('../logs/send.log', 'a')
                sys.stdout = log_file
                sys.stderr = log_file
                
                try:
                    update_config()  # Reload config to ensure STATUS is active
                    # Pass date parameters to ambil_data if provided
                    ambil_data(date_from=date_from, date_to=date_to)
                finally:
                    log_file.flush()
                    log_file.close()
                    sys.stdout = sys.__stdout__
                    sys.stderr = sys.__stderr__
            
            # Run in a thread to avoid blocking
            import threading
            thread = threading.Thread(target=manual_send_wrapper)
            thread.daemon = True
            thread.start()
            
            send_type = 'filtered' if (date_from and date_to) else 'all'
            return jsonify({
                'success': True,
                'message': f'Pengiriman manual {send_type} berhasil dipicu untuk {pending_count} data. Periksa log untuk detail.',
                'count': pending_count,
                'type': send_type
            }), 200
            
        except Exception as send_error:
            print(f"[SEND] Error triggering send: {str(send_error)}")
            return jsonify({
                'success': False,
                'error': f'Failed to trigger send: {str(send_error)}'
            }), 500
    
    except Exception as e:
        print(f"[SEND] Unexpected error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/data/filter', methods=['POST'])
@login_required
def filter_data():
    """Filter data berdasarkan kriteria tertentu"""
    try:
        data = request.get_json()
        mysql_config = mysqlConfig()
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        # Build query with parameterized statements to prevent SQL injection
        table = data.get('table', 'data')  # 'data' atau 'klhk'
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        params = []
        
        # Debug logging
        print(f"[FILTER] Table: {table}, Date From: {date_from}, Date To: {date_to}")
        
        if table == 'data':
            # Filter pending data (belum terkirim) - query dari tmp table
            query = "SELECT * FROM tmp WHERE (status IS NULL OR status = '')"
            
            if date_from:
                query += " AND `date` >= %s"
                params.append(date_from)
            if date_to:
                query += " AND `date` <= %s"
                params.append(date_to)
            
            query += " ORDER BY `date` DESC LIMIT 1000"
        
        elif table == 'klhk':
            query = "SELECT * FROM klhk_json_encode_success WHERE 1=1"
            
            if date_from:
                query += " AND timestamp >= %s"
                params.append(date_from)
            if date_to:
                query += " AND timestamp <= %s"
                params.append(date_to)
            
            query += " ORDER BY timestamp DESC LIMIT 1000"
        
        print(f"[FILTER] Query: {query}")
        print(f"[FILTER] Params: {params}")
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        print(f"[FILTER] Result count: {len(rows)}")
        
        # Convert datetime
        for row in rows:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        # Load klhk_fields from config
        from config import loadConfig
        config = loadConfig()
        klhk_fields = config.get('klhk_fields', 'datetime,pH,cod,tss,nh3n,flow')
        
        return jsonify({
            'success': True,
            'count': len(rows),
            'taggal': f"{date_from} s/d {date_to}",
            'data': rows,
            'klhk_fields': klhk_fields
        }), 200
    
    except Exception as e:
        print(f"[FILTER ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/retry/filter', methods=['POST'])
@login_required
def filter_retry_data():
    """Filter data retry berdasarkan kriteria tertentu"""
    try:
        data = request.get_json()
        mysql_config = mysqlConfig()
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        # Build query with parameterized statements to prevent SQL injection
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        params = []
        
        query = "SELECT * FROM tmp WHERE status = 'retry'"
        
        if date_from:
            query += " AND `date` >= %s"
            params.append(date_from)
        if date_to:
            query += " AND `date` <= %s"
            params.append(date_to)
        
        query += " ORDER BY `date` DESC LIMIT 1000"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert datetime
        for row in rows:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(rows),
            'data': rows
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data/all', methods=['POST'])
@login_required
def get_all_data():
    """Mendapatkan semua data (union dari tabel data dan tmp)"""
    try:
        data = request.get_json()
        mysql_config = mysqlConfig()
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        params = []
        date_col = '`date`'
        
        # Build UNION query to get data from both data and tmp tables
        query = f"""
        SELECT * FROM (
            SELECT * FROM data WHERE 1=1
        """
        
        if date_from:
            query += f" AND {date_col} >= %s"
            params.append(date_from)
        if date_to:
            query += f" AND {date_col} <= %s"
            params.append(date_to)
        
        query += f"""
            UNION ALL
            SELECT * FROM tmp WHERE 1=1
        """
        
        if date_from:
            query += f" AND {date_col} >= %s"
            params.append(date_from)
        if date_to:
            query += f" AND {date_col} <= %s"
            params.append(date_to)
        
        query += f"""
        ) AS combined_data
        ORDER BY {date_col} DESC
        LIMIT 1000
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert datetime
        for row in rows:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
        
        # Get has_fields from config
        from config import loadConfig
        config = loadConfig()
        has_fields = config.get('has_fields', 'datetime,pH,cod,tss,nh3n,flow')
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(rows),
            'data': rows,
            'has_fields': has_fields
        }), 200
    
    except Exception as e:
        import traceback
        print(f"Error in get_all_data: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs/<log_type>', methods=['GET'])
@login_required
def get_logs(log_type):
    """Mendapatkan log files dari folder logs"""
    try:
        # Validasi log_type
        valid_logs = ['web','sensor', 'send', 'retry', 'has-send', 'backup']
        if log_type not in valid_logs:
            return jsonify({'success': False, 'error': 'Invalid log type'}), 400
        
        logs_dir = '../logs'
        log_file = os.path.join(logs_dir, f'{log_type}.log')
        
        # Check if file exists
        if not os.path.exists(log_file):
            return jsonify({
                'success': True,
                'count': 0,
                'data': [],
                'message': f'Log file {log_type}.log not found'
            }), 200
        
        # Read log file - last N lines
        lines = []
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                # Get last 1000 lines
                lines = all_lines[-1000:]
        except Exception as e:
            return jsonify({'success': False, 'error': f'Error reading log file: {str(e)}'}), 500
        
        # Format log lines with timestamp and sequence number
        formatted_logs = []
        for idx, line in enumerate(lines):
            formatted_logs.append({
                'no': len(lines) - idx,  # Reverse numbering (highest first)
                'message': line.strip(),
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'success': True,
            'count': len(formatted_logs),
            'data': formatted_logs,
            'log_type': log_type
        }), 200
    
    except Exception as e:
        import traceback
        print(f"Error in get_logs: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500




if __name__ == "__main__":
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT_NUMBER_APP
    app.run(host="0.0.0.0", port=port)
