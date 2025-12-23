import serial
import struct
import time

import os
from dotenv import load_dotenv

env_path = "/opt/logix/config/env"  # env file path
if not load_dotenv(dotenv_path=env_path):
    print(f"Error: env file not found at {env_path}")
    exit(1)

ISCAN_STATUS = os.getenv('ISCAN_STATUS')
ISCAN_PORT = os.getenv('ISCAN_PORT')

# Jumlah maksimum percobaan jika tidak ada respon dari sensor
MAX_RETRIES = 3

def read_modbus(port, request, crc):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            baudrate = 38400
            parity = serial.PARITY_ODD
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

def read_cod():
    return read_modbus(
        ISCAN_PORT,
        bytearray([0x02, 0x04, 0x00, 0x8A, 0x00, 0x02]),
        bytearray([0x50, 0x12])
    )

def read_tss():
    return read_modbus(
        ISCAN_PORT,
        bytearray([0x02, 0x04, 0x00, 0x82, 0x00, 0x02]),
        bytearray([0xD1, 0xD0])
    )

def read_temp():
    return read_modbus(
        ISCAN_PORT,
        bytearray([0x02, 0x04, 0x00, 0xBA, 0x00, 0x02]),
        bytearray([0x50, 0x1D])
    )



def get_iscan_data():
    """
    Membaca data dari sensor ISCAN.
    Jika sensor tidak aktif atau port tidak tersedia, return tuple berisi None.
    """

    if ISCAN_STATUS.lower() != "active":
        print("[INFO] Modul ISCAN tidak aktif. Melewati pembacaan data.")
        return (None,) * 3

    if not os.path.exists(ISCAN_PORT):
        print(f"[ERROR] Port {ISCAN_PORT} tidak tersedia. Membatalkan pembacaan.")
        return

    try:
        print("[INFO] Modul ISCAN aktif. Melakukan pembacaan data.")
        cod = read_cod()
        tss = read_tss()
        temp = read_temp()

        return cod, tss, temp

    except Exception as e:
        print(f"[ERROR] Gagal membaca data ISCAN: {e}")
        return (None,) * 3

