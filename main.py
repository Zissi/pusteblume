import pyb
import lcd160cr
import machine

# create LCD on the X pins
lcd = lcd160cr.LCD160CR('X')
lcd.set_pen(lcd.rgb(255, 0, 0), lcd.rgb(64, 64, 128))

# Erase lcd display when button is pressed
sw = pyb.Switch()
sw.callback(lambda: lcd.erase())

# create I2C peripheral at frequency of 400kHz
i2c = machine.I2C(sda=machine.Pin('Y10'), scl=machine.Pin('Y9'), freq=400000)
i2c.scan()

# create empty arrays to store current observations and images
b1 = bytearray(1)
b2 = bytearray(2)
image_buf = bytearray(10000)


def hdc1080_read(a=0):
    b1[0] = a
    i2c.writeto(64, b1)
    pyb.delay(20)
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


def display_pusteblume(hum, average_hum_diff, tmp, last_image):
    # turn off all interrupts. Switch interrupt (line 10) erases the display and crashes
    # if sth. writes to it at the same time.
    irq_state = pyb.disable_irq()
    with open('/sd/pusteblume/s_p_{}.jpg'.format(last_image), 'rb') as f:
        f.readinto(image_buf)
        lcd.set_pos(0, 0)
        lcd.jpeg(image_buf)
        lcd.set_pos(5, 110)
        lcd.set_font(1, scale=1)
        lcd.set_text_color(lcd.rgb(188, 234, 231), lcd.rgb(64, 64, 128))
        lcd.write('H ' + str(round(hum)) + ' ')
        lcd.set_pos(40, 130)
        lcd.write(str(round(average_hum_diff, 2)))

        lcd.set_pos(80, 110)
        lcd.set_font(1, scale=1)
        lcd.set_text_color(lcd.rgb(188, 234, 231), lcd.rgb(64, 64, 128))
        lcd.write('T ' + str(round(tmp)))
    pyb.enable_irq(irq_state)


def calculate_average_diff(observations):
    diffs = []
    for i, obs in enumerate(observations):
        if i < len(observations) - 1:
            diffs.append((observations[i + 1] - obs) / (obs + 1))

    return sum(diffs) / len(diffs)


def read_sensors(last_temperatures, last_humidities, last_image):
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
            display_pusteblume(hum, average_hum_diff, temp, last_image)
            if last_image != 28:
                last_image += 1

        elif average_hum_diff > 0.005 or hum > 90:
            display_pusteblume(hum, average_hum_diff, temp, last_image)
            if last_image != 1:
                last_image -= 1

    return last_temperatures, last_humidities, last_image


if __name__ == '__main__':

    last_temps = [0]
    last_hums = [0]
    last_image = 2

    while True:
        last_temps, last_hums, last_image = read_sensors(last_temps, last_hums, last_image)
