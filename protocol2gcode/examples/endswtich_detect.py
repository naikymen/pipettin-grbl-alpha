import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
from time import sleep

limit_pin = 14

GPIO.setwarnings(False)  # Ignore warning for now
GPIO.setmode(GPIO.BCM)   # Use physical pin numbering
GPIO.setup(limit_pin, GPIO.IN)

while True:  # Run forever
    if GPIO.input(limit_pin) == GPIO.LOW:
        print("Button was pushed!")
    sleep(0.01)
