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

PH200_PORT = os.getenv('PH200_PORT')
PH200_STATUS = os.getenv('PH200_STATUS')

MAX_RETRIES = 3
SERIAL_CFG = dict(baudrate=9600, bytesize=8, parity=serial.PARITY_NONE, stopbits=1, timeout=0.2)

def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return struct.pack("<H", crc)

def read_modbus(port, request, retries=MAX_RETRIES):
    packet = request + crc16(request)
    for attempt in range(1, retries + 1):
        try:
            with serial.Serial(port, **SERIAL_CFG) as ser:
                time.sleep(0.2)
                ser.write(packet)
                time.sleep(0.2)
                resp = ser.read(256)

            if len(resp) >= 7:
                return round(struct.unpack("<f", resp[3:7])[0], 2)

            msg = "No response" if not resp else "Incomplete response"
            print(f"Percobaan {attempt}/{retries}: {msg} from {port}, retrying...")
        except Exception as e:
            print(f"Percobaan {attempt}/{retries}: Error reading Modbus: {e}, retrying...")
        time.sleep(0.5)

    print(f"Gagal membaca data dari {port} setelah {retries} percobaan.")
    send_sensor_log(f"Gagal membaca data Sensor PH200 dari {port} setelah {retries} percobaan.")
    return None

def read_ph():
    return read_modbus(PH200_PORT, bytearray([0x01, 0x03, 0x00, 0x82, 0x00, 0x02]))

def read_wtemp():
    return read_modbus(PH200_PORT, bytearray([0x01, 0x03, 0x00, 0x80, 0x00, 0x02]))


def get_ph200_data():

    if PH200_STATUS.lower() != "active":
        print("[INFO] Modul PH200 tidak aktif. Melewati pembacaan data.")
        send_sensor_log("Konfigurasi Modul PH200 tidak aktif.")
        return None, None
    
    if not os.path.exists(PH200_PORT):
        print(f"Port {PH200_PORT} tidak tersedia. Membatalkan pembacaan data.")
        send_connection_log(f"Port {PH200_PORT} tidak tersedia.")
        return None, None
    
    try:
        print("[INFO] Modul PH200 aktif. Melakukan pembacaan data.")
        ph = read_ph()
        wtemp = read_wtemp()
        return ph, wtemp
    except Exception as e:
        print(f"Error saat membaca data PH200: {e}")
        send_sensor_log(f"Error saat membaca data Sensor PH200: {e}")
        return None, None



# if __name__ == "__main__":
#     try:
#         while True:
#             print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | pH={read_ph()} | wtemp={read_temp()}")
#             time.sleep(60)
#     except KeyboardInterrupt:
#         print("\nStopped by user.")