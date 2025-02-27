import RPi.GPIO as GPIO
import time

LDR_PIN = 18

GPIO.setmode(GPIO.BCM)

while True:
    reading = 0
    GPIO.setup(LDR_PIN, GPIO.OUT)
    GPIO.output(LDR_PIN, GPIO.LOW)
    time.sleep(1)
    GPIO.setup(LDR_PIN, GPIO.IN)
    while(GPIO.input(LDR_PIN) == GPIO.LOW):
        reading = reading + 1
    print (reading)
    time.sleep(1)
