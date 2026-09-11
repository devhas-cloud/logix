import serial
import struct
import time

def crc16_modbus(data: bytes) -> bytes:
    """
    Hitung CRC16 (Modbus RTU, poly 0xA001).
    Kembalikan 2 byte: [CRC_LO, CRC_HI].
    """
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return bytes([crc & 0xFF, (crc >> 8) & 0xFF])

def read_mace():
    try:
        port = "/dev/ttyAMA5"
        baudrate = 38400
        parity = serial.PARITY_ODD
        stopbits = serial.STOPBITS_ONE
        bytesize = serial.EIGHTBITS
        timeout = 1

        ser = serial.Serial(port, baudrate, bytesize, parity, stopbits, timeout)
        time.sleep(0.2) 

        # Request asli kamu, CRC sekarang dihitung otomatis
        request = bytearray([0x01, 0x04, 0x00, 0x82, 0x00, 0x02])
        crc = crc16_modbus(request)
        modbus_request = request + crc

        ser.write(modbus_request)
        time.sleep(0.2)  
        response = ser.read(256)

        if not response:
            print("No response received from MACE sensor")
            ser.close()
            return None
        
        if len(response) >= 7:  # dibiarkan sesuai kode kamu
            cod = round(struct.unpack('>f', response[3:7])[0], 2)
            #depth = round(struct.unpack('>f', response[7:11])[0], 2)
            #flow = round(struct.unpack('>f', response[11:15])[0], 2)
            #tflow = round(struct.unpack('>f', response[15:19])[0], 2)
        else:
            print("Incomplete response received from MACE sensor")
            ser.close()
            return None

        ser.close()
        return cod
    except Exception as e:
        print(f"Error in read_modbus4: {e}")
        return None

def get_mace_data():
    return read_mace()

# === Tambahan minimal agar bisa langsung jalan di terminal (serial monitor di terminal) ===
if __name__ == "__main__":
    try:
        while True:
            cod = read_mace()
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            if None in (cod):
                print(f"{ts} | ERROR/No data")
            else:
                print(f"{ts} | COD={cod}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped by user.")
