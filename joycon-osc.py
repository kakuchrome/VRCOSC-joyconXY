import hid
import time

VENDOR_ID = 0x057E
L_PRODUCT_ID = 0x2006
R_PRODUCT_ID = 0x2007

L_ACCEL_OFFSET_X = 350
L_ACCEL_OFFSET_Y = 0
L_ACCEL_OFFSET_Z = 4081
R_ACCEL_OFFSET_X = 350
R_ACCEL_OFFSET_Y = 0
R_ACCEL_OFFSET_Z = -4081

MY_PRODUCT_ID = L_PRODUCT_ID


import argparse
import random
import time

from pythonosc import udp_client


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--ip", default="127.0.0.1",
      help="The ip of the OSC server")
  parser.add_argument("--port", type=int, default=9000,
      help="The port the OSC server is listening on")
  args = parser.parse_args()

  client = udp_client.SimpleUDPClient(args.ip, args.port)



def write_output_report(joycon_device, packet_number, command, subcommand, argument):
    joycon_device.write(command
                        + packet_number.to_bytes(1, byteorder='big')
                        + b'\x00\x01\x40\x40\x00\x01\x40\x40'
                        + subcommand
                        + argument)

def is_left():
    return MY_PRODUCT_ID == L_PRODUCT_ID

def to_int16le_from_2bytes(hbytebe, lbytebe):
    uint16le = (lbytebe << 8) | hbytebe 
    int16le = uint16le if uint16le < 32768 else uint16le - 65536
    return int16le

def get_nbit_from_input_report(input_report, offset_byte, offset_bit, nbit):
    return (input_report[offset_byte] >> offset_bit) & ((1 << nbit) - 1)

def get_accel_x(input_report, sample_idx=0):
    if sample_idx not in [0, 1, 2]:
        raise IndexError('sample_idx should be between 0 and 2')
    return (to_int16le_from_2bytes(get_nbit_from_input_report(input_report, 13 + sample_idx * 12, 0, 8),
                                   get_nbit_from_input_report(input_report, 14 + sample_idx * 12, 0, 8))
            - (L_ACCEL_OFFSET_X if is_left() else R_ACCEL_OFFSET_X))

def get_accel_y(input_report, sample_idx=0):
    if sample_idx not in [0, 1, 2]:
        raise IndexError('sample_idx should be between 0 and 2')
    return (to_int16le_from_2bytes(get_nbit_from_input_report(input_report, 15 + sample_idx * 12, 0, 8),
                                   get_nbit_from_input_report(input_report, 16 + sample_idx * 12, 0, 8))
            - (L_ACCEL_OFFSET_Y if is_left() else R_ACCEL_OFFSET_Y))

def get_accel_z(input_report, sample_idx=0):
    if sample_idx not in [0, 1, 2]:
        raise IndexError('sample_idx should be between 0 and 2')
    return (to_int16le_from_2bytes(get_nbit_from_input_report(input_report, 17 + sample_idx * 12, 0, 8),
                                   get_nbit_from_input_report(input_report, 18 + sample_idx * 12, 0, 8))
            - (L_ACCEL_OFFSET_Z if is_left() else R_ACCEL_OFFSET_Z))

def get_gyro_x(input_report, sample_idx=0):
    if sample_idx not in [0, 1, 2]:
        raise IndexError('sample_idx should be between 0 and 2')
    return to_int16le_from_2bytes(get_nbit_from_input_report(input_report, 19 + sample_idx * 12, 0, 8),
                                  get_nbit_from_input_report(input_report, 20 + sample_idx * 12, 0, 8))

def get_gyro_y(input_report, sample_idx=0):
    if sample_idx not in [0, 1, 2]:
        raise IndexError('sample_idx should be between 0 and 2')
    return to_int16le_from_2bytes(get_nbit_from_input_report(input_report, 21 + sample_idx * 12, 0, 8),
                                  get_nbit_from_input_report(input_report, 22 + sample_idx * 12, 0, 8))

def get_gyro_z(input_report, sample_idx=0):
    if sample_idx not in [0, 1, 2]:
        raise IndexError('sample_idx should be between 0 and 2')
    return to_int16le_from_2bytes(get_nbit_from_input_report(input_report, 23 + sample_idx * 12, 0, 8),
                                  get_nbit_from_input_report(input_report, 24 + sample_idx * 12, 0, 8))

if __name__ == '__main__':

    joycon_device = hid.device()
    joycon_device.open(VENDOR_ID, MY_PRODUCT_ID)

    # 6軸センサーを有効化
    write_output_report(joycon_device, 0, b'\x01', b'\x40', b'\x01')
    # 設定を反映するためには時間間隔が必要
    time.sleep(0.02)
    # 60HzでJoy-Conの各データを取得するための設定
    write_output_report(joycon_device, 1, b'\x01', b'\x03', b'\x30')

    tailxvol = 0
    tailyvol = 0
    #reset to 0 0 
    client.send_message("/avatar/parameters/TailX", tailxvol)
    client.send_message("/avatar/parameters/TailY", tailyvol)


    while True:
        time.sleep(0.2)
        input_report = joycon_device.read(49)
        pointx1 = format(get_accel_x(input_report))
        pointy1 = format(get_accel_y(input_report))
        print("pt1" , pointx1 , pointy1)
        input_report = joycon_device.read(49)
        time.sleep(0.2)
        pointx2 = format(get_accel_x(input_report))
        pointy2 = format(get_accel_y(input_report))
        print("pt2" , pointx2 , pointy2)
        if pointx1 > pointx2:
            tailxvol = tailxvol - 0.1
        else:
            tailxvol = tailxvol + 0.1

        if  tailxvol >= 1:
            tailxvol = 1
        elif tailxvol < -1:
            tailxvol = -1
        
        if pointy1 > pointy2:
            tailyvol = tailyvol - 0.1
        else:
            tailyvol = tailyvol + 0.1

        if  tailyvol >= 1:
            tailyvol = 1
        elif tailyvol < -1:
            tailyvol = -1

        print(tailxvol , tailyvol)
        client.send_message("/avatar/parameters/TailX", tailxvol)
        client.send_message("/avatar/parameters/TailY", tailyvol)

            
        # 加速度センサー
        # print("Accel X : {:8d}".format(get_accel_x(input_report)))
        # print("Accel Y : {:8d}".format(get_accel_y(input_report)))
        # print("Accel Z : {:8d}".format(get_accel_z(input_report)))


        # client.send_message("/avatar/parameters/TailX", format(get_accel_x(input_report)))
        # client.send_message("/avatar/parameters/TailY", format(get_accel_y(input_report)))
        

        # print("Accel : {:8d} {:8d} {:8d}".format(get_accel_x(input_report),
        #                                          get_accel_y(input_report),
        #                                          get_accel_z(input_report)))
        # # ジャイロセンサー
        # print("Gyro  : {:8d} {:8d} {:8d}".format(get_gyro_x(input_report),
        #                                          get_gyro_y(input_report),
        #                                          get_gyro_z(input_report)))
        print()
