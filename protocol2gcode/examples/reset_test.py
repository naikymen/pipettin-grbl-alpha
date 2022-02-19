from RPi import GPIO
import time

reset_bcm_pin = 2

GPIO.setmode(GPIO.BCM)
GPIO.setup(reset_bcm_pin, GPIO.OUT)
GPIO.output(reset_bcm_pin, 0) # Low 0V (note that high is only 3.3V, not 5V)
time.sleep(0.333)
GPIO.output(reset_bcm_pin, 1) # Low 0V (note that high is only 3.3V, not 5V)
GPIO.cleanup()
