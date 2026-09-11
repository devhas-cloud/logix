import serial
import struct
import time

# Jumlah maksimum percobaan jika tidak ada respon dari sensor
MAX_RETRIES = 3

def calculate_crc16(data):
    """
    Fungsi untuk menghitung Modbus CRC-16 secara otomatis.
    Menggunakan polynomial 0xA001.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    # Modbus RTU menggunakan format Little-Endian (LSB dikirim lebih dulu)
    return struct.pack('<H', crc)

def read_modbus(port, request):
    # Hitung CRC secara otomatis dan gabungkan dengan request
    crc_bytes = calculate_crc16(request)
    modbus_request = request + crc_bytes

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            baudrate = 9600
            parity = serial.PARITY_NONE
            stopbits = serial.STOPBITS_ONE
            bytesize = serial.EIGHTBITS
            timeout = 0.2

            ser = serial.Serial(port, baudrate, bytesize, parity, stopbits, timeout)
            time.sleep(0.2)

            ser.write(modbus_request)
            time.sleep(0.2)  # Tunggu respons
            response = ser.read(256)

            if not response:
                print(f"Percobaan {attempt}/{MAX_RETRIES}: No response from {port}, retrying...")
                ser.close()
                time.sleep(0.5)  # Tunggu sebelum mencoba lagi
                continue

            if len(response) >= 7:  # Pastikan respons cukup panjang
                data = round(struct.unpack('<f', response[3:7])[0], 2)
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

# Fungsi pembacaan sekarang tidak perlu menyertakan CRC di akhir
def read_ph():
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x16, 0x00, 0x02]))

def read_orp(): 
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x18, 0x00, 0x02]))

def read_do():
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x22, 0x00, 0x02]))

def read_turb():
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x1C, 0x00, 0x02]))

def read_tss():
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x1E, 0x00, 0x02]))

def read_conduct():
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x0A, 0x00, 0x02]))

def read_tds():
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x10, 0x00, 0x02]))

def read_nh3n():
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x3C, 0x00, 0x02]))

def read_cod():
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x60, 0x00, 0x02]))

def read_bod():
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x60, 0x00, 0x02]))

def read_temp():
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x00, 0x00, 0x02]))

def read_wpress():
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x02, 0x00, 0x02]))

def read_depth():
    return read_modbus("/dev/ttyAMA5", bytearray([0x01, 0x03, 0x01, 0x04, 0x00, 0x02]))

def get_ds502_data():
    ph = read_ph()
    orp = read_orp()
    do = read_do()
    turb = read_turb()
    tss = read_tss()
    conduct = read_conduct()
    tds = read_tds()
    nh3n = read_nh3n()
    cod = read_cod()
    bod = read_bod()
    temp = read_temp()
    WPress = read_wpress()
    depth = read_depth()
    return ph, orp, do, turb, tss, conduct, tds, nh3n, cod, bod, temp, WPress, depth

#========= Tambahan minimal agar bisa langsung jalan dari terminal (serial monitor) =========
if __name__ == "__main__":
    try:
        while True:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            ph, orp, do, turb, tss, conduct, tds, nh3n, cod, bod, temp, WPress, depth = get_ds502_data()
            # Tampilkan ke terminal seperti serial monitor
            print(
                f"{ts} | pH={ph} | ORP={orp} | DO={do} | TURB={turb} | TSS={tss} | CONDUCT={conduct} | TDS={tds} | NH3N={nh3n} | COD={cod} | BOD={bod} | TEMP={temp} | WPress={WPress} | DEPTH={depth}"
            )
            time.sleep(60)  # interval refresh tampilan
    except KeyboardInterrupt:
        print("\nStopped by user.")