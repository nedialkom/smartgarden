import grovepi
import math
import time

# Sensors connected on:
# D3: Digital temperature moisture sensor (DHT)
# A0: Soil humidity sensor
# A1: Sound sensor
# A2: Light sensor


def get_moisture():
    # NOTE:
    #           The wiki:      Observer:
    # 		    Min  Typ  Max  value    Condition
    # 		    0    0    0    0        sensor in open air
    # 		    0    20   300  18       sensor in dry soil
    # 		    300  580  700  425      sensor in humid soil
    # 		    700  940  950  690      sensor in water
    sensor = 0
    try:
        return grovepi.analogRead(sensor)
    except IOError:
        return None


def get_dht():
    dht_port = 3
    try:
        [temp, humidity] = grovepi.dht(3, 0)
        i = 1
        while math.isnan(temp) is True and math.isnan(humidity) is True:
            [temp, humidity] = grovepi.dht(dht_port, 0)
            if i == 100:
                print('Could not get dht in 100 attempts')
                break
            i = i + 1
        return temp, humidity
    except IOError:
        print("Error to get dht")


def get_sound():
    sensor = 1
    try:
        return grovepi.analogRead(sensor)
    except IOError:
        return None


def get_light():
    sensor = 2
    try:
        return grovepi.analogRead(sensor)
    except IOError:
        return None


def get_data():
    """
    Returns soil moisture, air temperature, air humidity, sound level, light level.
    """
    [t, h] = get_dht()
    return {'timestamp': int(round(time.time() * 1000)),
            "moisture": get_moisture(),
            "temperature": t,
            "humidity": h,
            "sound": get_sound(),
            "light": get_light()}


def relay(state):
    relay_port = 4
    grovepi.pinMode(relay_port, "OUTPUT")
    try:
        if state == 'on':
            grovepi.digitalWrite(relay_port, 1)
            print("relay is now on")
            return True
        elif state == 'off':
            grovepi.digitalWrite(relay_port, 0)
            print("relay is now off")
            return True
        else:
            return False
    except IOError:
        return False


if __name__ == '__main__':
    print('Soil moisture: ', get_moisture())
    [temperature, hum] = get_dht()
    print('Air temperature: ', temperature, ' C')
    print('Air humidity:', hum, ' %')
    print('Sound level:', get_sound())
    print('Light level:', get_light())
    print(get_data())
