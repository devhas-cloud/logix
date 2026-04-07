import serial
import struct
import time
import os
from config import loadConfig
from logsSend import send_network_log, send_connection_log, send_sensor_log

CONFIG_DB = loadConfig()

RT200_STATUS = CONFIG_DB.get('rt200_status', 'inactive')
PORT_SERIAL = CONFIG_DB.get('rt200_port', '/dev/ttyAMA4')

# Jumlah maksimum percobaan jika tidak ada respon dari sensor
MAX_RETRIES = 5

def read_modbus(parameter,port, request, crc):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            baudrate = 19200
            parity = serial.PARITY_EVEN
            stopbits = serial.STOPBITS_ONE
            bytesize = serial.EIGHTBITS
            timeout = 1

            ser = serial.Serial(port, baudrate, bytesize, parity, stopbits, timeout)
            time.sleep(0.5)

            modbus_request = request + crc
            ser.write(modbus_request)
            time.sleep(0.5)  # Tunggu respons
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
                time.sleep(1)
                continue

        except Exception as e:
            print(f"Percobaan {attempt}/{MAX_RETRIES}: Error reading Modbus: {e}, retrying...")
            time.sleep(1)  # Tunggu sebelum mencoba lagi

    print(f"Gagal membaca data dari {port} setelah {MAX_RETRIES} percobaan.")
    send_sensor_log(f"Gagal membaca data RT200 - {parameter} dari {port} setelah {MAX_RETRIES} percobaan.")
    return None  # Kembalikan None jika gagal membaca setelah 3 percobaan

def read_temp():
    return read_modbus(
        "temp",
        PORT_SERIAL,
        bytearray([0x05, 0x03, 0x00, 0x2D, 0x00, 0x02]),
        bytearray([0x55, 0x86])
    )

def read_press():
    return read_modbus(
        "press",
        PORT_SERIAL,
        bytearray([0x05, 0x03, 0x00, 0x25, 0x00, 0x02]),
        bytearray([0xD4, 0x44])
    )

def read_depth():
    return read_modbus(
        "depth",
        PORT_SERIAL,
        bytearray([0x05, 0x03, 0x00, 0x35, 0x00, 0x02]),
        bytearray([0xD5, 0x81])
    )

def get_rt200_data():
    global CONFIG_DB, RT200_STATUS, PORT_SERIAL
    
    # Reload config untuk memastikan perubahan konfigurasi langsung diterapkan
    CONFIG_DB = loadConfig()
    RT200_STATUS = CONFIG_DB.get('rt200_status', 'inactive')
    PORT_SERIAL = CONFIG_DB.get('rt200_port', '/dev/ttyAMA4')
    
    if RT200_STATUS.lower() != "active":
        print("[INFO] Modul RT200 tidak aktif. Melewati pembacaan data.")
        send_sensor_log("Konfigurasi Modul RT200 tidak aktif.")
        return None, None, None

    if not os.path.exists(PORT_SERIAL):
        print(f"Port {PORT_SERIAL} tidak tersedia. Membatalkan semua pembacaan.")
        send_connection_log(f"Port RT200 {PORT_SERIAL} tidak tersedia.")
        return
    else:
        print("[INFO] Modul RT200 aktif. Melakukan pembacaan data.")  
        wtemp = read_temp()
        wpress = read_press()
        depth = round((read_depth() * 30.48),2)  # Konversi dari feet ke cm
        return wtemp, wpress, depth


# # Tambahan untuk menjalankan langsung
# if __name__ == "__main__":
#     while True:
#         temp, press, depth = get_rt200_data()
#         print(f"Temperature: {temp}, Pressure: {press}, Depth: {depth}")
#         time.sleep(10)
