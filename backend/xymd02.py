import serial
import struct
import time
import os
from dotenv import load_dotenv
from logsSend import send_network_log, send_connection_log, send_sensor_log

env_path = "/home/pi/logix/config/.env"  # env file path
if not load_dotenv(dotenv_path=env_path):
    print(f"Error: env file not found at {env_path}")
    exit(1)

XYMD02_PORT = "/dev/ttySC0"  # Default port, can be overridden by env variable
XYMD02_STATUS = os.getenv('XYMD02_STATUS')
XYMD02_SLAVE_ID = int(os.getenv('XYMD02_SLAVE_ID', 1))  # Default ke 1 jika tidak ada di env

PORT_NAME = XYMD02_PORT
BAUDRATE = 9600
SLAVE_ID = XYMD02_SLAVE_ID
TEMP_REG = 1
HUM_REG = 2

def calc_crc(msg):
    crc = 0xFFFF
    for pos in msg:
        crc ^= pos
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')

def read_register(port, slave_id, reg_addr):
    msg = bytearray([slave_id, 0x04, (reg_addr >> 8) & 0xFF, reg_addr & 0xFF, 0x00, 0x01])
    bytearray([0x01, 0x04, 0x00, 0x01, 0x00, 0x02])
    msg += calc_crc(msg)
    port.write(msg)
    time.sleep(0.1)
    resp = port.read(7)
    if len(resp) == 7 and resp[1] == 0x04:
        return resp[3] << 8 | resp[4]
    else:
        return None


def get_xymd02_data():

    if XYMD02_STATUS.lower() != "active":
        print("[INFO] Modul XYMD02 tidak aktif. Melewati pembacaan data.")
        send_sensor_log("Konfigurasi Modul XYMD02 tidak aktif.")
        return None, None
    
    if not os.path.exists(XYMD02_PORT):
        print(f"Port {XYMD02_PORT} tidak tersedia. Membatalkan pembacaan data.")
        send_connection_log(f"Port {XYMD02_PORT} tidak tersedia.")
        return None, None
    
    try:
        print("[INFO] Modul XYMD02 aktif. Melakukan pembacaan data.")
        with serial.Serial(PORT_NAME, BAUDRATE, timeout=0.5) as ser:
            atemp = read_register(ser, SLAVE_ID, TEMP_REG)
            hum  = read_register(ser, SLAVE_ID, HUM_REG)

            if atemp is not None and hum is not None:
                return round(atemp/10, 1), round(hum/10, 1)
            else:
                print("Failed to read sensor")
                send_sensor_log("Gagal membaca data Sensor XYMD02.")
                return None, None
    except Exception as e:
        print(f"Error saat membaca data XYMD02: {e}")
        send_sensor_log(f"Error saat membaca data Sensor XYMD02: {e}")
        return None, None




# with serial.Serial(PORT_NAME, BAUDRATE, timeout=0.5) as ser:
#     while True:
#         temp = read_register(ser, 1, TEMP_REG)
#         hum  = read_register(ser, 1, HUM_REG)
#         #if temp is not None and hum is not None:
#         print(f"Temperature: {temp/10:.1f} °C, Humidity: {hum/10:.1f} %")
#         # else:
#         #     print("Failed to read sensor")
#         time.sleep(10)
