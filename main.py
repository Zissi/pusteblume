#from tilt_lights import light_on_tilt
#from breath_led import breath_led
#from display_tilt import display_tilt
#from temp import read_sensors
#from pusteblume import read_sensors
import pyb

# Display output on LCD
#uart = pyb.UART('XA', 115200)
#pyb.repl_uart(uart)

import lcd160cr
from time import sleep
import machine

lcd = lcd160cr.LCD160CR('X')
sw = pyb.Switch()
sw.callback(lambda:lcd.erase())

i2c = machine.I2C(sda=machine.Pin('Y10'), scl=machine.Pin('Y9'), freq=400000)
i2c.scan()

dt = 20
b1 = bytearray(1)
b2 = bytearray(2)

last_temp = [0]
last_hum = [0]
last_image = 2




def hdc1080_read(a=0):
    b1[0] = a
    i2c.writeto(64, b1)
    pyb.delay(dt)
    i2c.readfrom_into(64, b2)
    return (b2[0] << 8) | b2[1]


# calculating temperature
def hdc_temp():
    t = hdc1080_read(0)
    return (t / 0x10000) * 165 - 40


# calculating humidity
def hdc_hum():
    t = hdc1080_read(1)
    return (t / 0x10000) * 100


def read_sensors():
    lcd.set_pen(lcd.rgb(255, 0, 0), lcd.rgb(64, 64, 128))
    temp = hdc_temp()
    hum = hdc_hum()

    global last_temp
    global last_hum
    global last_image
    global images

    if abs(last_hum[-1] - hum) > 1 or abs(last_temp[-1] - temp) > 1:
        last_hum.append(hum)
        last_temp.append(temp)
        print("T: %.2f" % (temp))
        print("H:  %.2f" % (hum))
        if len(last_hum) > 10:
            last_hum = last_hum[1:]
            last_temp = last_temp[1:]
    diffs = []
    if len(last_hum) > 5:
        for i, hum in enumerate(last_hum):
            if i < len(last_hum) - 1:
                diffs.append((last_hum[i + 1] - hum) / (hum + 1))
        diff = sum(diffs) / len(diffs)
        print(diff)
        if diff < 0:
            buf = bytearray(10000)
            with open('/sd/pusteblume/s_p_{}.jpg'.format(last_image), 'rb') as f:
                f.readinto(buf)
                lcd.set_pos(0,0)
                lcd.jpeg(buf)
                lcd.set_pos(50,110)
                lcd.set_font(1, scale=1)
                lcd.set_text_color(lcd.rgb(188, 234, 231), lcd.rgb(64, 64, 128))
                print(last_hum[-1])
                print(str(round(last_hum[-1])))
                lcd.write(str(round(last_hum[-1])))
                lcd.set_pos(50,130)
                lcd.write(str(round(diff, 2)))
            if last_image == 28:
                last_image = 28
            else:
                last_image += 1
        elif diff > 0.01 or hum > 90:
            buf = bytearray(10000)
            with open('/sd/pusteblume/s_p_{}.jpg'.format(last_image), 'rb') as f:
                f.readinto(buf)
                lcd.set_pos(0,0)
                lcd.jpeg(buf)
                lcd.set_pos(50,110)
                lcd.set_font(1, scale=1)
                lcd.set_text_color(lcd.rgb(188, 234, 231), lcd.rgb(64, 64, 128))
                lcd.write(str(round(last_hum[-1])))
                lcd.set_pos(50,130)
                lcd.write(str(round(diff, 2)))

                if last_image == 1:
                    last_image = 1
                else:
                    last_image -= 1



while True:
    read_sensors()
    #display_tilt()
    #light_on_tilt()


