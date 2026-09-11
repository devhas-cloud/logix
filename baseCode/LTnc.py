import serial
import struct
import time

# Jumlah maksimum percobaan jika tidak ada respon dari sensor
MAX_RETRIES = 3

def read_modbus(port, request, crc):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            baudrate = 19200
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

def read_depth():
    return read_modbus(
        "/dev/ttyAMA5",
        bytearray([0x01, 0x03, 0x17, 0xF8, 0x00, 0x02]),
        bytearray([0x40, 0x4E])
    )

def get_ltnc_data():
    depth = round(read_depth()/100,2)
    flow = round(1.34*(depth*depth),2)
    return depth, flow

#========= Tambahan minimal agar bisa langsung jalan dari terminal (serial monitor) =========
if __name__ == "__main__":
    try:
        while True:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            depth, flow = get_ltnc_data()
            # Tampilkan ke terminal seperti serial monitor
            print(
                f"{ts} | Depth={depth} | Flow={flow}"
            )
            time.sleep(60)  # interval refresh tampilan
    except KeyboardInterrupt:
        print("\nStopped by user.")
