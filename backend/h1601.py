import serial
import struct
import time
import os
from dotenv import load_dotenv
from logsSend import send_network_log, send_connection_log, send_sensor_log

env_path = "/opt/logix/config/env"  # env file path
if not load_dotenv(dotenv_path=env_path):
    print(f"Error: env file not found at {env_path}")
    exit(1)

H1601_PORT = os.getenv('H1601_PORT')
H1601_STATUS = os.getenv('H1601_STATUS')

MAX_RETRIES = 5
SERIAL_CFG = dict(baudrate=9600, bytesize=8, parity=serial.PARITY_NONE, stopbits=1, timeout=0.2)

def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return struct.pack("<H", crc)

def to_hex(data):
    return " ".join(f"{b:02X}" for b in data)

def read_modbus(port, request, retries=MAX_RETRIES):
    packet = request + crc16(request)

    for attempt in range(1, retries + 1):
        try:
            #print(f"\n[{port}] Percobaan {attempt}/{retries}")
            #print(f"TX HEX: {to_hex(packet)}")

            with serial.Serial(port, **SERIAL_CFG) as ser:
                time.sleep(0.2)
                ser.write(packet)
                time.sleep(0.2)
                resp = ser.read(256)

            print(f"RX HEX: {to_hex(resp) if resp else '(kosong)'}")

            if len(resp) >= 7:
                value = round(struct.unpack(">f", resp[3:7])[0], 2)
                print(f"Parsed value: {value}")
                return value

            msg = "No response" if not resp else "Incomplete response"
            print(f"Percobaan {attempt}/{retries}: {msg} from {port}, retrying...")

        except Exception as e:
            print(f"Percobaan {attempt}/{retries}: Error reading Modbus: {e}, retrying...")

        time.sleep(1)

    print(f"Gagal membaca data dari {port} setelah {retries} percobaan.")
    send_sensor_log(f"Gagal membaca data Sensor H1601 dari {port} setelah {retries} percobaan.")
    return None

def read_depth():
    return read_modbus(H1601_PORT, bytearray([0x01, 0x03, 0x00, 0x12, 0x00, 0x02]))

def read_velocity():
    return read_modbus(H1601_PORT, bytearray([0x01, 0x03, 0x00, 0x16, 0x00, 0x02]))

def read_flow():
    return read_modbus(H1601_PORT, bytearray([0x01, 0x03, 0x00, 0x18, 0x00, 0x02]))



def get_h1601_data():

    if H1601_STATUS.lower() != "active":
        print("[INFO] Modul H1601 tidak aktif. Melewati pembacaan data.")
        send_sensor_log("Konfigurasi Modul H1601 tidak aktif.")
        return None, None
    
    if not os.path.exists(H1601_PORT):
        print(f"Port {H1601_PORT} tidak tersedia. Membatalkan pembacaan data.")
        send_connection_log(f"Port {H1601_PORT} tidak tersedia.")
        return None, None
    
    try:
        print("[INFO] Modul H1601 aktif. Melakukan pembacaan data.")
        depth = read_depth()
        flow = read_flow()/60
        return depth, flow

    except Exception as e:
        print(f"Error saat membaca data H1601: {e}")
        send_sensor_log(f"Error saat membaca data H1601: {e}")
        return None, None



# if __name__ == "__main__":
#     try:
#         while True:
#             print(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
#             depth = read_depth()
#             #velocity = read_velocity()
#             flow = read_flow()/60
#             print(f"RESULT | depth={depth} | velocity={velocity} | flow={flow}")
#             #print(f"RESULT | flow={flow}")
#             time.sleep(10)
#     except KeyboardInterrupt:
#         print("\nStopped by user.")