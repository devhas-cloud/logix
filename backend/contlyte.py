import serial
import struct
import time
import os
from dotenv import load_dotenv

env_path = "/opt/logix/config/env"  # env file path
if not load_dotenv(dotenv_path=env_path):
    print(f"Error: env file not found at {env_path}")
    exit(1)

CONTLYTE_PORT = os.getenv('CONTLYTE_PORT')
CONTLYTE_STATUS = os.getenv('CONTLYTE_STATUS')

# Jumlah maksimum percobaan jika tidak ada respon dari sensor
MAX_RETRIES = 3

def read_modbus(port, request, crc):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            baudrate = 38400
            parity = serial.PARITY_EVEN
            stopbits = serial.STOPBITS_ONE
            bytesize = serial.EIGHTBITS
            timeout = 1

            ser = serial.Serial(port, baudrate, bytesize, parity, stopbits, timeout)
            time.sleep(0.2)

            modbus_request = request + crc
            ser.write(modbus_request)
            time.sleep(0.2)  # Tunggu respons
            response = ser.read(256)

            if not response:
                print(f"Percobaan {attempt}/{MAX_RETRIES}: No response from {port}, retrying...")
                ser.close()
                time.sleep(0.5)  # Tunggu sebelum mencoba lagi
                continue

            if len(response) >= 7:  # Pastikan respons cukup panjang
                data = round(struct.unpack('>f', response[3:7])[0], 2)
                ser.close()
                return data
            else:
                print(f"Percobaan {attempt}/{MAX_RETRIES}: Incomplete response from {port}, retrying...")
                ser.close()
                time.sleep(0.5)
                continue

        except Exception as e:
            print(f"Percobaan {attempt}/{MAX_RETRIES}: Error reading Modbus: {e}, retrying...")
            time.sleep(0.5)  # Tunggu sebelum mencoba lagi

    print(f"Gagal membaca data dari {port} setelah {MAX_RETRIES} percobaan.")
    return None  # Kembalikan None jika gagal membaca setelah 3 percobaan

def read_ph():
    return read_modbus(
        CONTLYTE_PORT,
        bytearray([0x02, 0x04, 0x00, 0x82, 0x00, 0x02]),
        bytearray([0xD1, 0xD0])
    )

def read_tss():
    return read_modbus(
        CONTLYTE_PORT,
        bytearray([0x02, 0x04, 0x00, 0x8A, 0x00, 0x02]),
        bytearray([0x50, 0x12])
    )

def read_cod():
    return read_modbus(
        CONTLYTE_PORT,
        bytearray([0x02, 0x04, 0x00, 0x92, 0x00, 0x02]),
        bytearray([0xD0, 0x15])
    )

def read_temp():
    return read_modbus(
        CONTLYTE_PORT,
        bytearray([0x02, 0x04, 0x00, 0x9A, 0x00, 0x02]),
        bytearray([0x51, 0xD7])
    )

def get_conlyte_data():

    if CONTLYTE_STATUS != "active":
        print("[INFO] Modul CONTLYTE tidak aktif. Melewati pembacaan data.")
        return None, None, None, None

    if not os.path.exists(CONTLYTE_PORT):
        print(f"Port {CONTLYTE_PORT} tidak tersedia. Membatalkan semua pembacaan.")
        return

    else:
        print("[INFO] Modul CONTLYTE aktif. Melakukan pembacaan data.")
        ph = read_ph()
        tss = read_tss()
        cod = read_cod()
        temp = read_temp()
        return ph, tss, cod, temp

# #========= Tambahan minimal agar bisa langsung jalan dari terminal (serial monitor) =========
# if __name__ == "__main__":
#     try:
#         while True:
#             ts = time.strftime("%Y-%m-%d %H:%M:%S")
#             ph, tss, cod, temp = get_conlyte_data()
#             # Tampilkan ke terminal seperti serial monitor
#             print(
#                 f"{ts} | PH={ph} | TSS={tss} | COD={cod} | TEMP={temp}"
#             )
#             time.sleep(60)  # interval refresh tampilan
#     except KeyboardInterrupt:
#         print("\nStopped by user.")
