import serial
import time
import os
import traceback
from config import loadConfig

# ===============================
# Config
# ===============================
CONFIG_DB = loadConfig()

SEM5096_STATUS = CONFIG_DB.get("sem5096_status", "active")
SEM5096_PORT = CONFIG_DB.get("sem5096_port", "/dev/ttySC0")

BAUDRATE = 9600
SERIAL_TIMEOUT = 0.5
WRITE_TIMEOUT = 0.5
RETRY = 3
DELAY_BETWEEN_WRITE_READ = 0.18  # detik


class SEM5096:
    def __init__(self, status=SEM5096_STATUS, port=SEM5096_PORT, baudrate=BAUDRATE):
        self.status = status
        self.port_name = port
        self.baudrate = baudrate
        self.ser = None
        self.open_port()


    def open_port(self):
        try:
            self.ser = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=SERIAL_TIMEOUT,
                write_timeout=WRITE_TIMEOUT,
                exclusive=True
            )
            # Flush buffers
            time.sleep(0.15)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            print(f"[INFO] Port {self.port_name} berhasil dibuka.")
        except Exception as e:
            print(f"[ERROR] Gagal membuka port {self.port_name}: {e}")
            traceback.print_exc()
            self.ser = None

    def close_port(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"[INFO] Port {self.port_name} ditutup.")

    def read_data(self):
        """Baca sensor SEM5096, return tuple (atemp, hum, apress, wspeed, wdir, rain, srad)"""
        if self.status.lower() != "active":
            print("[INFO] Modul SEM5096 tidak aktif. Skip pembacaan.")
            return (None, None, None, None, None, None, None)

        if not self.ser or not self.ser.is_open:
            print("[ERROR] Serial port tidak tersedia.")
            return (None, None, None, None, None, None, None)

        # Modbus request SEM5096
        request = bytearray([0xFF, 0x03, 0x00, 0x09, 0x00, 0x07, 0xC1, 0xD4])

        for attempt in range(1, RETRY + 1):
            try:
                # Flush FIFO sebelum request
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()

                self.ser.write(request)
                self.ser.flush()

                time.sleep(DELAY_BETWEEN_WRITE_READ)

                response = self.ser.read(64)

                if not response or len(response) < 17:
                    print(f"[WARN] Response pendek (attempt {attempt}): {response}")
                    time.sleep(0.1)
                    continue

                # Parsing sensor
                atemp = round(int.from_bytes(response[3:5], "big") / 100 - 40, 2)
                hum = round(int.from_bytes(response[5:7], "big") / 100, 2)
                apress = round(int.from_bytes(response[7:9], "big") / 10, 2)
                wspeed = round(int.from_bytes(response[9:11], "big") / 100, 2)
                wdir = round(int.from_bytes(response[11:13], "big") / 10, 2)
                rain = round(int.from_bytes(response[13:15], "big") / 10, 2)
                srad = int.from_bytes(response[15:17], "big")

                return (atemp, hum, apress, wspeed, wdir, rain, srad)

            except Exception as e:
                print(f"[ERROR] Gagal membaca sensor (attempt {attempt}): {e}")
                traceback.print_exc()
                time.sleep(0.2)

        print("[ERROR] Semua percobaan membaca sensor gagal.")
        return (None, None, None, None, None, None, None)

def get_sem5096_data():
  
    # Reload config untuk memastikan perubahan konfigurasi langsung diterapkan
    CONFIG_DB = loadConfig()
    SEM5096_STATUS = CONFIG_DB.get("sem5096_status", "active")
    SEM5096_PORT = CONFIG_DB.get("sem5096_port", "/dev/ttySC0")
    
    # Gunakan nilai config terbaru yang baru di-reload
    sensor = SEM5096(status=SEM5096_STATUS, port=SEM5096_PORT, baudrate=BAUDRATE)
    data = sensor.read_data()
    sensor.close_port()
    return data

# ===============================
# Test langsung
# ===============================

# if __name__ == "__main__":
#     sensor = SEM5096()
#     data = sensor.read_data()
#     if data[0] is not None:
#         print("✅ Sensor data:", data)
#     else:
#         print("❌ Gagal membaca data sensor.")
#     sensor.close_port()