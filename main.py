import pyb
import lcd160cr
import machine

lcd = lcd160cr.LCD160CR('X')
sw = pyb.Switch()
sw.callback(lambda: lcd.erase())

i2c = machine.I2C(sda=machine.Pin('Y10'), scl=machine.Pin('Y9'), freq=400000)
i2c.scan()

dt = 20
b1 = bytearray(1)
b2 = bytearray(2)


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


def display_pusteblume(hum, average_hum_diff, tmp):
    buf = bytearray(10000)
    with open('/sd/pusteblume/s_p_{}.jpg'.format(last_image), 'rb') as f:
        f.readinto(buf)
        lcd.set_pos(0, 0)
        lcd.jpeg(buf)
        lcd.set_pos(5, 110)
        lcd.set_font(1, scale=1)
        lcd.set_text_color(lcd.rgb(188, 234, 231), lcd.rgb(64, 64, 128))
        lcd.write('H ' + str(round(hum)))
        lcd.set_pos(40, 130)
        lcd.write(str(round(average_hum_diff, 2)))

        lcd.set_pos(80, 110)
        lcd.set_font(1, scale=1)
        lcd.set_text_color(lcd.rgb(188, 234, 231), lcd.rgb(64, 64, 128))
        lcd.write('T ' + str(round(tmp)))


def calculate_average_diff(observations):
    diffs = []
    for i, obs in enumerate(observations):
        if i < len(observations) - 1:
            diffs.append((observations[i + 1] - obs) / (obs + 1))

    return sum(diffs) / len(diffs)


def read_sensors(last_temperatures, last_humidities, last_image):
    lcd.set_pen(lcd.rgb(255, 0, 0), lcd.rgb(64, 64, 128))
    temp = hdc_temp()
    hum = hdc_hum()

    if abs(last_humidities[-1] - hum) > 0.5 or abs(last_temperatures[-1] - temp) > 0.5:
        last_humidities.append(hum)
        last_temperatures.append(temp)

        if len(last_humidities) > 5:
            last_humidities = last_humidities[1:]
            last_temperatures = last_temperatures[1:]

        average_hum_diff = calculate_average_diff(last_humidities)

        if average_hum_diff < 0:
            display_pusteblume(hum, average_hum_diff, temp)

            if last_image != 28:
                last_image += 1

        elif average_hum_diff > 0.005 or hum > 90:
            display_pusteblume(hum, average_hum_diff, temp)

            if last_image != 1:
                last_image -= 1

    return last_temperatures, last_humidities, last_image


last_temperatures = [0]
last_humidities = [0]
last_image = 2

while True:
    last_temperatures, last_humidities, last_image = read_sensors(last_temperatures, last_humidities, last_image)
