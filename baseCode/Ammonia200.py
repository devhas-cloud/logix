import serial, struct, time

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
    return None

def read_nh3n():
    return read_modbus("/dev/ttyAMA5", bytearray([0x04, 0x03, 0x00, 0x82, 0x00, 0x02]))

if __name__ == "__main__":
    try:
        while True:
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | NH3-N={read_nh3n()}")
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopped by user.")