import serial
import time

def calc_crc(msg):
    crc = 0xFFFF
    for pos in msg:
        crc ^= pos
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')


def read_register(port, slave_id, reg_addr):
    try:
        msg = bytearray([
            slave_id,
            0x04,
            (reg_addr >> 8) & 0xFF,
            reg_addr & 0xFF,
            0x00,
            0x01
        ])

        msg += calc_crc(msg)

        print("SEND :", msg.hex(" "))

        port.write(msg)
        time.sleep(0.1)

        resp = port.read(7)

        print("RECV :", resp.hex(" "), "LEN:", len(resp))

        if len(resp) < 5:
            print("ERROR: response terlalu pendek")
            return None

        if resp[1] == 0x84:
            print("MODBUS EXCEPTION CODE:", resp[2])
            return None

        if resp[1] != 0x04:
            print("ERROR: function code tidak sesuai:", resp[1])
            return None

        value = resp[3] << 8 | resp[4]
        return value

    except Exception as e:
        print("ERROR read_register:", e)
        return None


PORT_NAME = '/dev/ttySC0'
BAUDRATE = 9600
SLAVE_ID = 1
TEMP_REG = 1
HUM_REG = 2

try:
    with serial.Serial(PORT_NAME, BAUDRATE, timeout=0.5) as ser:
        print("Serial opened:", ser.name)

        while True:
            temp = read_register(ser, SLAVE_ID, TEMP_REG)
            hum  = read_register(ser, SLAVE_ID, HUM_REG)

            if temp is not None and hum is not None:
                print(f"Temperature: {temp/10:.1f} °C, Humidity: {hum/10:.1f} %")
            else:
                print("Failed to read sensor")

            print("-" * 40)
            time.sleep(1)

except Exception as e:
    print("Serial error:", e)