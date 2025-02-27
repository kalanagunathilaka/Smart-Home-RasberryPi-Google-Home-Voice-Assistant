import adafruit_dht
import board
import time

DHT_SENSOR = adafruit_dht.DHT11(board.D14)

while True:
    try:
        temperature = DHT_SENSOR.temperature
        humidity = DHT_SENSOR.humidity

        if humidity is not None and temperature is not None:
            print(f"Temp={temperature:0.1f}C Humidity={humidity:0.1f}%")
        else:
            print("Sensor failure. Check wiring.")
    except RuntimeError as error:
        print(f"Error reading sensor: {error}")

    time.sleep(2)