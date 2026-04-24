import mysql.connector
import sqlite3
import os
import pytz
import time
from datetime import datetime

CONFIG_DIR = "../config"
CONFIG_DB_NAME = "config.db"
CONFIG_DB_PATH = os.path.join(CONFIG_DIR, CONFIG_DB_NAME)

# Flag untuk mencegah multiple initialization
_CONFIG_INITIALIZED = False


def defaultConfig():
    global _CONFIG_INITIALIZED
    
    config_dir = CONFIG_DIR
    db_path = CONFIG_DB_PATH

    # Pastikan folder config ada
    os.makedirs(config_dir, exist_ok=True)

    # Cek apakah database sudah ada dan valid
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Cek apakah tabel config sudah ada dan berisi data
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='config'")
            config_table_exists = cursor.fetchone()[0] > 0
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='satuan'")
            satuan_table_exists = cursor.fetchone()[0] > 0
            
            if config_table_exists and satuan_table_exists:
                cursor.execute("SELECT COUNT(*) FROM config WHERE id=1")
                config_data_exists = cursor.fetchone()[0] > 0
                cursor.execute("SELECT COUNT(*) FROM satuan WHERE id=1")
                satuan_data_exists = cursor.fetchone()[0] > 0
                
                if config_data_exists and satuan_data_exists:
                    if not _CONFIG_INITIALIZED:
                        print(f"Database already initialized: {db_path}")
                        _CONFIG_INITIALIZED = True
                    cursor.close()
                    conn.close()
                    return  # Database sudah ada, tidak perlu reinisialisasi
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Existing database has issues: {e}, will reinitialize...")

    conn = None
    cursor = None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if not _CONFIG_INITIALIZED:
            print(f"Initializing SQLite database: {db_path}")
            _CONFIG_INITIALIZED = True

        # Buat tabel config
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY,

            -- general
            port_number_app TEXT,
            port_number_log TEXT,
            timezone TEXT,

            -- database
            db_host TEXT,
            db_port TEXT,
            db_name TEXT,
            db_user TEXT,
            db_password TEXT,

            -- sensor devices
            at500_status TEXT,
            at500_port TEXT,

            rt200_status TEXT,
            rt200_port TEXT,

            sem5096_status TEXT,
            sem5096_port TEXT,

            mace_status TEXT,
            mace_port TEXT,

            iscan_status TEXT,
            iscan_port TEXT,

            ltnc_status TEXT,
            ltnc_port TEXT,

            spectro_status TEXT,
            spectro_ip TEXT,
            spectro_port TEXT,

            contlyte_status TEXT,
            contlyte_port TEXT,

            ds502_status TEXT,
            ds502_port TEXT,

            ammonia200_status TEXT,
            ammonia200_port TEXT,

            cod200x_status TEXT,
            cod200x_port TEXT,

            h1601_status TEXT,
            h1601_port TEXT,

            ph200_status TEXT,
            ph200_port TEXT,

            tss200x_status TEXT,
            tss200x_port TEXT,

            xymd02_status TEXT,
            xymd02_port TEXT,
            xymd02_slave_id TEXT,

            delay INTEGER,


            -- klhk api
            klhk_status TEXT,
            klhk_api_url TEXT,
            klhk_token_url TEXT,
            klhk_uid TEXT,
            klhk_fields TEXT,
            klhk_max_dup_retry TEXT,
            klhk_target_minute TEXT,

            -- has api
            has_status TEXT,
            has_api_url TEXT,
            has_token_api TEXT,
            has_fields TEXT,

            -- has logs
            has_logs_api_url TEXT,
            has_logs_token_api TEXT,

            -- dashboard/web
            parameters TEXT,
            gap_web TEXT,
            web_title TEXT,
            web_name TEXT,
            web_username TEXT,
            web_password TEXT,

            -- device info
            device_id TEXT,
            location_name TEXT,
            software_version TEXT,
            geo_latitude TEXT,
            geo_longitude TEXT
        )
        """)

        if not _CONFIG_INITIALIZED:
            print("Table 'config' created")

        configurations = {
            # general
            "port_number_app": "5010",
            "port_number_log": "3000",
            "timezone": "Asia/Jakarta",

            # database
            "db_host": "127.0.0.1",
            "db_port": "3306",
            "db_name": "logix",
            "db_user": "logix",
            "db_password": "logix",

            
            # =====================================================
            #                 SENSOR DEVICES
            # =====================================================

            # --- Sensor AT500 ---
            # Options: active / inactive
            'at500_status': 'inactive',
            'at500_port': '/dev/ttyAMA3',

            # --- Sensor RT200 ---
            # Options: active / inactive
            'rt200_status': 'inactive',
            'rt200_port': '/dev/ttyAMA4',

            # --- Sensor SEM5096 ---
            # Options: active / inactive
            'sem5096_status': 'active',
            'sem5096_port': '/dev/ttySC0',

            # --- Sensor MACE ---
            # Options: active / inactive
            'mace_status': 'inactive',
            'mace_port': '/dev/ttyAMA5',

            # --- Sensor ISCAN ---
            # Options: active / inactive
            'iscan_status': 'inactive',
            'iscan_port': '/dev/ttyAMA5',


            # --- Sensor LTNC ---
            # Options: active / inactive
            'ltnc_status': 'inactive',
            'ltnc_port': '/dev/ttyAMA5',


            # --- Sensor SPECTRO ---
            # Options: active / inactive
            'spectro_status': 'inactive',
            'spectro_ip': '192.168.1.100',
            'spectro_port': '502',

            # --- Sensor CONTLYTE ---
            # Options: active / inactive
            'contlyte_status': 'inactive',
            'contlyte_port': '/dev/ttyAMA5',

            # --- Sensor DS502 ---
            # Options: active / inactive
            'ds502_status': 'inactive',
            'ds502_port': '/dev/ttyAMA5',


            # -- Sensor AMMONIA 200 ---
            # Options: active / inactive
            'ammonia200_status': 'inactive',
            'ammonia200_port': '/dev/ttyAMA5',

            # --- Sensor COD200X ---
            # Options: active / inactive
            'cod200x_status': 'inactive',
            'cod200x_port': '/dev/ttyAMA5',

            # --- Sensor H1601 ---
            # Options: active / inactive
            'h1601_status': 'inactive',
            'h1601_port': '/dev/ttyAMA3',

            # --- Sensor PH200 ---
            # Options: active / inactive
            'ph200_status': 'inactive',
            'ph200_port': '/dev/ttyAMA5',


            # --- Sensor TSS200X ---
            # Options: active / inactive
            'tss200x_status': 'inactive',
            'tss200x_port': '/dev/ttyAMA5',


            # --- Sensor XYMD02 ---
            # Options: active / inactive
            'xymd02_status': 'inactive',
            'xymd02_port': '/dev/ttySC0',
            'xymd02_slave_id': '1',


            # --- Sensor Interval ---
            # Delay pembacaan (menit)
            'delay': '2',

            # klhk api
            'klhk_status': 'inactive',
            'klhk_api_url': 'https://sparing.kemenlh.go.id/api/send-hourly-vendor',
            'klhk_token_url': 'https://sparing.kemenlh.go.id/api/secret-sensor',
            'klhk_uid': '',
            'klhk_fields': 'datetime,pH,cod,tss,nh3n,flow',
            'klhk_max_dup_retry': '3',
            'klhk_target_minute': '10',

            # has api
            "has_status": "inactive",
            "has_api_url": "https://api.hasportal.com/api/v1/data",
            "has_token_api": "",
            "has_fields": "datetime,pH,cod,tss,nh3n,flow,wtemp,orp,turb,tds,conduct,do,depth,bod,wpress",

            # has logs
            "has_logs_token_api": "",

            # dashboard/web
            "parameters": "pH,cod,tss,nh3n,flow,wtemp,orp,turb,tds,conduct,do,depth,bod,wpress",
            "gap_web": "3",
            "web_title": "WQMS",
            "web_name": "Water Quality Monitoring System",
            "web_username": "admin",
            "web_password": "has123456",

            # device info
            "device_id": "HSP-xxxxxx",
            "location_name": "PT. Has Environmental",
            "software_version": "1.0.0",
            "geo_latitude": "-6.5224399",
            "geo_longitude": "106.8384747"
        }

        # Buat table satuan jika belum ada
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS satuan (
            id INTEGER PRIMARY KEY,
            satuan_ph TEXT,
            satuan_cod TEXT,
            satuan_tss TEXT,
            satuan_nh3n TEXT,
            satuan_flow TEXT,
            satuan_atemp TEXT,
            satuan_wtemp TEXT,
            satuan_orp TEXT,
            satuan_turb TEXT,
            satuan_tds TEXT,
            satuan_conduct TEXT,
            satuan_do TEXT,
            satuan_salinity TEXT,
            satuan_battery TEXT,
            satuan_depth TEXT,
            satuan_tflow TEXT,
            satuan_no3 TEXT,
            satuan_bod TEXT,
            satuan_apress TEXT,
            satuan_wpress TEXT,
            satuan_hum TEXT,
            satuan_wspeed TEXT,
            satuan_wdir TEXT,
            satuan_rain TEXT,
            satuan_srad TEXT
        )
        """)
        if not _CONFIG_INITIALIZED:
            print("Table 'satuan' created")


        configurations_satuan = {
            "satuan_ph": "pH",
            "satuan_cod": "mg/L",
            "satuan_tss": "mg/L",
            "satuan_nh3n": "mg/L",
            "satuan_flow": "L/s",
            "satuan_atemp": "°C",
            "satuan_wtemp": "°C",
            "satuan_orp": "mV",
            "satuan_turb": "NTU",
            "satuan_tds": "mg/L",
            "satuan_conduct": "µS/cm",
            "satuan_do": "mg/L",
            "satuan_salinity": "ppt",
            "satuan_battery": "V",
            "satuan_depth": "m",
            "satuan_tflow": "L/s",
            "satuan_no3": "mg/L",
            "satuan_bod": "mg/L",
            "satuan_apress": "mbar",
            "satuan_wpress": "mbar",
            "satuan_hum": "%",
            "satuan_wspeed": "m/s",
            "satuan_wdir": "°",
            "satuan_rain": "mm",
            "satuan_srad": "W/m²"
        }

        # Check if config with id=1 already exists
        cursor.execute("SELECT COUNT(*) as count FROM config WHERE id=1")
        exists = cursor.fetchone()[0] > 0
        
        # Only insert default values if config doesn't exist
        if not exists:
            columns = ", ".join(configurations.keys())
            placeholders = ", ".join(["?"] * len(configurations))
            values = list(configurations.values())

            cursor.execute(f"""
            INSERT INTO config (id, {columns})
            VALUES (1, {placeholders})
            """, values)
            if not _CONFIG_INITIALIZED:
                print(f"Default config inserted into database")

        # Check if satuan with id=1 already exists
        cursor.execute("SELECT COUNT(*) as count FROM satuan WHERE id=1")
        satuan_exists = cursor.fetchone()[0] > 0

        if not satuan_exists:
            columns_satuan = ", ".join(configurations_satuan.keys())
            placeholders_satuan = ", ".join(["?"] * len(configurations_satuan))
            values_satuan = list(configurations_satuan.values())

            cursor.execute(f"""
            INSERT INTO satuan (id, {columns_satuan})
            VALUES (1, {placeholders_satuan})
            """, values_satuan)
            if not _CONFIG_INITIALIZED:
                print(f"Default satuan inserted into database")

        # Commit all changes
        conn.commit()
        if not _CONFIG_INITIALIZED:
            print(f"Database initialization complete: {db_path}")
            _CONFIG_INITIALIZED = True

    except Exception as e:
        print(f"Error pada defaultConfig: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def loadConfig():
    defaultConfig()
    conn = sqlite3.connect(CONFIG_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM config WHERE id=1")
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    config = dict(zip(columns, row))
    cursor.close()
    conn.close()
    return config

def mysqlConfig():
    config = loadConfig()
    HOST = config['db_host']
    USER = config['db_user']
    PASSWORD = config['db_password']
    DATABASE = config['db_name']
    PORT = config['db_port']
    
    
    # MySQL connection configuration
    MYSQL_CONFIG = {
        'host': HOST,
        'user': USER,
        'password': PASSWORD,
        'database': DATABASE,
        'port': PORT
    }

    return MYSQL_CONFIG


# === Initialize Global MYSQL_CONFIG ===
try:
    MYSQL_CONFIG = mysqlConfig()
except Exception as e:
    print(f"Warning: Could not initialize MYSQL_CONFIG at module load: {e}")
    MYSQL_CONFIG = {}


def ambilDateAll():
    tz = loadConfig()['timezone']
    tz = pytz.timezone(tz)
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    return timestamp

def ambilDate():
    tz = loadConfig()['timezone']
    tz = pytz.timezone(tz)
    date = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    return date

def ambilDateTime():
    tz = loadConfig()['timezone']
    tz = pytz.timezone(tz)
    Interval_Timestamp = datetime.strptime(ambilDateAll(), '%Y-%m-%d %H:%M:%S')
    unix_dt = int(time.mktime(Interval_Timestamp.timetuple()))
    return unix_dt
      
def cekTable():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        # Buat tabel jika belum ada
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                device TEXT,
                `date` DATETIME,
                datetime BIGINT DEFAULT 0,
                pH FLOAT DEFAULT 0,
                orp FLOAT DEFAULT 0,
                tds FLOAT DEFAULT 0,
                conduct FLOAT DEFAULT 0,
                do FLOAT DEFAULT 0,
                salinity FLOAT DEFAULT 0,
                nh3n FLOAT DEFAULT 0,
                battery FLOAT DEFAULT 0,
                depth FLOAT DEFAULT 0,
                flow FLOAT DEFAULT 0,
                tflow FLOAT DEFAULT 0,
                turb FLOAT DEFAULT 0,
                tss FLOAT DEFAULT 0,
                cod FLOAT DEFAULT 0,
                bod FLOAT DEFAULT 0,
                no3 FLOAT DEFAULT 0,
                atemp FLOAT DEFAULT 0,
                wtemp FLOAT DEFAULT 0,
                apress FLOAT DEFAULT 0,
                wpress FLOAT DEFAULT 0,
                hum FLOAT DEFAULT 0,
                wspeed FLOAT DEFAULT 0,
                wdir FLOAT DEFAULT 0,
                rain FLOAT DEFAULT 0,
                srad FLOAT DEFAULT 0,
                status TEXT,
                keterangan TEXT,
                dateterkirim DATETIME,
                has INT DEFAULT 0 
            )
        ''')
        conn.commit()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tmp (
                id INT AUTO_INCREMENT PRIMARY KEY,
                device TEXT,
                `date` DATETIME,
                datetime BIGINT DEFAULT 0,
                pH FLOAT DEFAULT 0,
                orp FLOAT DEFAULT 0,
                tds FLOAT DEFAULT 0,
                conduct FLOAT DEFAULT 0,
                do FLOAT DEFAULT 0,
                salinity FLOAT DEFAULT 0,
                nh3n FLOAT DEFAULT 0,
                battery FLOAT DEFAULT 0,
                depth FLOAT DEFAULT 0,
                flow FLOAT DEFAULT 0,
                tflow FLOAT DEFAULT 0,
                turb FLOAT DEFAULT 0,
                tss FLOAT DEFAULT 0,
                cod FLOAT DEFAULT 0,
                bod FLOAT DEFAULT 0,
                no3 FLOAT DEFAULT 0,
                atemp FLOAT DEFAULT 0,
                wtemp FLOAT DEFAULT 0,
                apress FLOAT DEFAULT 0,
                wpress FLOAT DEFAULT 0,
                hum FLOAT DEFAULT 0,
                wspeed FLOAT DEFAULT 0,
                wdir FLOAT DEFAULT 0,
                rain FLOAT DEFAULT 0,
                srad FLOAT DEFAULT 0,
                status TEXT,
                keterangan TEXT,
                dateterkirim DATETIME,
                has INT DEFAULT 0 
            )
        ''')
        conn.commit()
        
        #buat tabel  klhk json encode sukses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS klhk_json_encode_success (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                payload TEXT,
                response TEXT,
                date_send TEXT DEFAULT NULL,
                row_send INT DEFAULT 0,
                status BOOLEAN DEFAULT 0

            )
        ''')
        conn.commit()


        # Penambahan filed created_at untuk mencatat waktu pembuatan data, jika sudah ada tidak akan menambah kolom baru
        # Check if column exists before adding it (compatible with MySQL < 8.0)
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='data' AND COLUMN_NAME='created_at'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE data ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='tmp' AND COLUMN_NAME='created_at'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE tmp ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        conn.commit()
        
        # Penambahan filed category untuk membedakan jenis pengiriman data ke KLHK, jika sudah ada tidak akan menambah kolom baru
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='klhk_json_encode_success' AND COLUMN_NAME='category'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE klhk_json_encode_success ADD COLUMN category TEXT DEFAULT NULL")


        
    except Exception as e:
        print(f"[{datetime.now()}] Error pada koneksi database: {e}")
        return    

def insert_data(date,  datetime, ph, orp, tds, conduct, do, salinity, nh3n, battery, depth, flow, tflow, turb, tss, cod, bod, no3, atemp,wtemp, apress, wpress, hum, wspeed, wdir, rain, srad):
    
    device = loadConfig()['device_id']
    cekTable()        
    query = """
        INSERT INTO tmp (device, date, datetime, ph, orp, tds, conduct, do, salinity, nh3n, battery, depth, flow, tflow, turb, tss, cod, bod, no3, atemp,wtemp, apress, wpress, hum, wspeed, wdir, rain, srad)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        values = (
                device,
                date, datetime,
                ph, orp, tds, conduct, do, salinity, nh3n, battery, depth, flow, tflow, turb, tss, cod, bod, no3, atemp,wtemp, apress, wpress, hum, wspeed, wdir, rain, srad
            )
            #values = tuple("NULL" if v is None else v for v in values) # ganti jika None menjadi 0
        cursor.execute(query, values)
        conn.commit()

        print(f"[INFO] Data berhasil dimasukkan: {values}")
    except Exception as e:
        print(f"[ERROR] Gagal memasukkan data ke database: {e}")
    finally:
        # Tutup koneksi
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()



def insert_data_klhk_success(timestamp, payload, response, date_send=None, row_send=0, status=False, category=None):
    try:
        MYSQL_CONFIG = mysqlConfig()
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        query = """
        INSERT INTO klhk_json_encode_success (timestamp, payload, response, date_send, row_send, status, category)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """

        values = (timestamp, payload, response, date_send, row_send, status, category)
        cursor.execute(query, values)
        conn.commit()

    except Exception as e:
        print(f"[ERROR] Gagal memasukkan data ke klhk_json_encode_success: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()