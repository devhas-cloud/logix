import time
import os
from at500 import get_at500_data
from mace import get_mace_data
from spectro import read_modbus_tcp
from rt200 import get_rt200_data
from sem5096 import get_sem5096_data
from iscan import get_iscan_data 
from ltnc import get_ltnc_data 
from config import insert_data, ambilDate, ambilDateTime
from datetime import datetime
from dotenv import load_dotenv
from contlyte import get_conlyte_data
import sqlite3
import pytz

# Load environment variables
env_path = "/opt/logix/config/env"
if not load_dotenv(dotenv_path=env_path):
    print(f"Error: env file not found at {env_path}")
    exit(1)

# Configuration from environment variables
DELAY = int(os.getenv('DELAY'))
AT500_STATUS = os.getenv('AT500_STATUS')
MACE_STATUS = os.getenv('MACE_STATUS')
SPECTRO_STATUS = os.getenv('SPECTRO_STATUS')
RT200_STATUS = os.getenv('RT200_STATUS')
SEM5096_STATUS = os.getenv('SEM5096_STATUS')
ARG314_STATUS = os.getenv('ARG314_STATUS')
ISCAN_STATUS = os.getenv('ISCAN_STATUS')
LTNC_STATUS = os.getenv('LTNC_STATUS')
CONTLYTE_STATUS = os.getenv('CONTLYTE_STATUS')

# SQLite Database GPIO
DB_PATH = os.getenv("SQLITE_DB_PATH", "/opt/logix/data/gpio_logix.db")

def connect_db():
    """Membuka koneksi ke database SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def get_sensor_gpio(current_date, sensor, auto_delete=True):
    """
    Mengambil data terbaru dari tabel gpio berdasarkan nama sensor dan datetime tertentu.
    
    Argumen:
        sensor (str): nama sensor, misalnya 'rain_sensor'
        current_date (str): waktu dalam format 'YYYY-MM-DD HH:MM:SS'
        auto_delete (bool): jika True, hapus data lama di tanggal yang sama setelah dibaca.
        
    Return:
        float | None: nilai sensor terbaru pada tanggal yang sama, atau None jika tidak ada data.
    """
    
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Ambil data terbaru di tanggal yang sama dengan current_date
        cursor.execute("""
            SELECT id, `date`, nilai 
            FROM gpio
            WHERE sensor = ?
              AND `date` = ?
            ORDER BY `date` DESC
            LIMIT 1;
        """, (sensor, current_date))
        result = cursor.fetchone()
 
        if result:
            latest_id, latest_date, nilai = result

            if auto_delete:
                # Hapus semua data ketika data sudah diambil
                cursor.execute("""
                    DELETE FROM gpio
                    WHERE sensor = ?
                      AND `date` <= ?
                """, (sensor, current_date))
                conn.commit()
                print(f"[GPIO] 🔄 Hapus data lama sensor '{sensor}' ")

            print(f"[GPIO] ✅ Data terbaru sensor '{sensor}' untuk {latest_date}: {nilai}")
            return nilai
        else:
            print(f"[GPIO] ⚠️ Tidak ada data sensor '{sensor}' untuk tanggal {current_date}")
            return None

    except Exception as e:
        print(f"[ERROR] Gagal mengambil data dari database: {e}")
        return None

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()



def should_run():
    """Check if the script should run based on the current time and DELAY setting."""
    now = datetime.now()
    return now.minute % DELAY == 0 and now.second == 0


def main():
    current_date = ambilDate()
    print(f"[{current_date}] ⏱️ Service dimulai. Menunggu waktu eksekusi sensor setiap {DELAY} menit.")
    last_run = None
    
    # Initialize variables with default values (None)
    # ph, orp, tds, conduct, do, salinity, nh3n = (None,) * 7
    # battery, depth, flow, tflow = (None,) * 4
    # turb, tss, cod, bod, no3, wtemp = (None,) * 6
    # wpress, hum, wspeed, wdir, rain, srad = (None,) * 6
    
    try:
        while True:
            ph, orp, tds, conduct, do, salinity, nh3n = (None,) * 7
            battery, depth, flow, tflow = (None,) * 4
            turb, tss, cod, bod, no3, atemp, wtemp = (None,) * 7
            apress, wpress, hum, wspeed, wdir, rain, srad = (None,) * 7
            now = datetime.now()
            if should_run():
                # Ensure we don't run twice at the same time
                if last_run != now.replace(second=0, microsecond=0):
                    current_date = ambilDate()
                    current_datetime = ambilDateTime()
                    print(f"\n[{current_date}] 📡 Membaca semua sensor...")
                    
                    status_filter = True
                    
                    # === AT500 ===
                    if AT500_STATUS.lower() == "active":
                        at500_data = get_at500_data()
                        if at500_data:
                            new_ph, new_orp, new_tds, new_conduct, new_do, new_salinity, new_nh3n = at500_data
                            # Update global variables only if new data is not None
                            ph = new_ph if new_ph is not None else ph
                            orp = new_orp if new_orp is not None else orp
                            tds = new_tds if new_tds is not None else tds
                            conduct = new_conduct if new_conduct is not None else conduct
                            do = new_do if new_do is not None else do
                            salinity = new_salinity if new_salinity is not None else salinity
                            nh3n = new_nh3n if new_nh3n is not None else nh3n
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data AT500.")
                    
                    # === RT200 ===
                    if RT200_STATUS.lower() == "active":
                        rt200_data = get_rt200_data()
                        if rt200_data:
                            new_temp, new_press, new_depth = rt200_data
                            # Update global variables only if new data is not None
                            wtemp = new_temp if new_temp is not None else wtemp
                            wpress = new_press if new_press is not None else wpress
                            depth = new_depth if new_depth is not None else depth
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data RT200.")
                    
                    # === SEM5096 ===
                    if SEM5096_STATUS.lower() == "active":
                        sem5096_data = get_sem5096_data()
                        if sem5096_data:
                            new_temp, new_hum, new_press, new_wspeed, new_wdir, new_rain, new_srad = sem5096_data
                            # Update global variables only if new data is not None
                            atemp = new_temp if new_temp is not None else atemp
                            hum = new_hum if new_hum is not None else hum
                            apress = new_press if new_press is not None else apress
                            wspeed = new_wspeed if new_wspeed is not None else wspeed
                            wdir = new_wdir if new_wdir is not None else wdir
                            rain = new_rain if new_rain is not None else rain
                            srad = new_srad if new_srad is not None else srad
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data SEM5096.")
                    
                    
                    # === MACE ===
                    if MACE_STATUS.lower() == "active":
                        mace_data = get_mace_data()
                        if mace_data:
                            new_battery, new_depth, new_flow, new_tflow = mace_data
                            # Update global variables only if new data is not None
                            battery = new_battery if new_battery is not None else battery
                            depth = new_depth if new_depth is not None else depth
                            flow = new_flow if new_flow is not None else flow
                            tflow = new_tflow if new_tflow is not None else tflow
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data MACE.")
                    
                    # === SPECTRO ===
                    if SPECTRO_STATUS.lower() == "active":
                        modbus_data = read_modbus_tcp()
                        if modbus_data:
                            new_turb, new_tss, new_cod, new_bod, new_no3, new_temp = modbus_data
                            # Update global variables only if new data is not None
                            turb = new_turb if new_turb is not None else turb
                            tss = new_tss if new_tss is not None else tss
                            cod = new_cod if new_cod is not None else cod
                            bod = new_bod if new_bod is not None else bod
                            no3 = new_no3 if new_no3 is not None else no3
                            wtemp = new_temp if new_temp is not None else wtemp
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data Modbus TCP.")
                            
                    # === ISCAN ===
                    if ISCAN_STATUS.lower() == "active":
                        iscan_data = get_iscan_data()
                        if iscan_data:
                            new_cod, new_tss, new_temp = iscan_data
                            # Update global variables only if new data is not None
                            cod = new_cod if new_cod is not None else cod
                            tss = new_tss if new_tss is not None else tss
                            wtemp = new_temp if new_temp is not None else wtemp
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data ISCAN.")
                            
                            
                            
                    # === LTNC ===
                    if LTNC_STATUS.lower() == "active":
                        ltnc_data = get_ltnc_data()
                        if ltnc_data:
                            new_depth, new_flow = ltnc_data
                            depth = new_depth if new_depth is not None else depth
                            flow = new_flow if new_flow is not None else flow
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data LTNC.")

                    # === CONTLYTE ===
                    if CONTLYTE_STATUS.lower() == "active":
                        from contlyte import get_conlyte_data
                        contlyte_data = get_conlyte_data()
                        if contlyte_data:
                            new_ph, new_tss, new_cod, new_temp = contlyte_data
                            # Update global variables only if new data is not None
                            ph = new_ph if new_ph is not None else ph
                            tss = new_tss if new_tss is not None else tss
                            cod = new_cod if new_cod is not None else cod
                            wtemp = new_temp if new_temp is not None else wtemp
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data CONTLYTE.")
                    
                    # === GPIO Sensors ARG314 ===
                    if ARG314_STATUS.lower() == "active":
                        time.sleep(4)   #jika GPIO aktif delay 4 detik agar tidak bentrok saat pengambilan data
                        data = get_sensor_gpio(current_date,"rain_sensor")
                        # Update global variable only if new data is not None
                        rain = data if data is not None else rain
                        
                    
                    # Save data if all active sensors were read successfully
                    if status_filter:
                        # Check if any sensor is active
                        if all(status.lower() != "active" for status in [AT500_STATUS, MACE_STATUS, SPECTRO_STATUS, SEM5096_STATUS, RT200_STATUS, ISCAN_STATUS, LTNC_STATUS, CONTLYTE_STATUS, ARG314_STATUS]):
                            print(f"[{current_date}] ⚠️ Semua modul sensor tidak aktif. Melewati penyimpanan data.")
                        else:
                            print(f"[{current_date}] ✅ Semua data sensor berhasil terbaca.")
                            print("\n=== SENSOR DATA ===")
                            print(f"→ pH: {ph}, ORP: {orp}, TDS: {tds}, Conductivity: {conduct}, DO: {do}, Salinity: {salinity}, NH3-N: {nh3n}")
                            print(f"→ Battery: {battery}, Depth: {depth}, Flow: {flow}, TFlow: {tflow}")
                            print(f"→ Turbidity: {turb}, TSS: {tss}, COD: {cod}, BOD: {bod}, NO3: {no3}, atemp: {atemp}, wtemp: {wtemp}")
                            print(f"→ apress: {apress} wpress: {wpress} Hum: {hum}, WSpeed: {wspeed}, WDir: {wdir}, Rain: {rain}, SRad: {srad}")
                            print("===================  \n")
                            
                            insert_data(
                                current_date,
                                current_datetime,
                                ph, orp, tds, conduct, do, salinity, nh3n,
                                battery, depth, flow, tflow,
                                turb, tss, cod, bod, no3, atemp, wtemp,
                                apress,wpress, hum, wspeed, wdir, rain, srad
                            ) 
                    else:
                        print(f"[{current_date}] ❌ Tidak semua sensor berhasil terbaca. Data tidak disimpan.")
                    
                    last_run = now.replace(second=0, microsecond=0)
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print(f"\n[{current_date}] 🛑 Service dihentikan secara manual.")

if __name__ == "__main__":
    main()