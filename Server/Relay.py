import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

RELAY_PIN = 20

# Set up GPIO pin as output
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Turn on the relay (device ON)
GPIO.output(RELAY_PIN, GPIO.HIGH)
print("Relay ON")

time.sleep(5)

# Turn off the relay (device OFF)
GPIO.output(RELAY_PIN, GPIO.LOW)
print("Relay OFF")

GPIO.cleanup()
