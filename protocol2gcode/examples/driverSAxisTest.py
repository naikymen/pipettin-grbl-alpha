#!/usr/bin/python3

from time import sleep
from RPi import GPIO
from math import ceil, floor
import pigpio
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--move', help='Millimeters')
args = parser.parse_args()
displacement = float(args.move)

class LimitSwitchException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'LimitSwitchException: the limit switch has been activated, {0} '.format(self.message)
        else:
            return 'LimitSwitchException has been raised!'


class SAxisPigpio(object):
    def __init__(self, microstep="1/32", delay_default=0.0208,
                 SPR=200, MPR=8,
                 MODE=(17, 27, 22),  # MODE=(14, 15, 18)
                 limit_pin=14, DIR=20, STEP=21,
                 pwm_freq=500, pwm_duty=128, accel_interval=0.5*80/1000):

        self.MODE = MODE            # Microstep Resolution GPIO Pins
        self.microstep = microstep  # Microstep choice
        self.RESOLUTION = {'1':    [1, (0, 0, 0)],
                           '1/2':  [2, (1, 0, 0)],
                           '1/4':  [4, (0, 1, 0)],
                           '1/8':  [8, (1, 1, 0)],
                           '1/16': [16, (0, 0, 1)],
                           '1/32': [32, (1, 0, 1)]
                           }
        self.microstep_int = self.RESOLUTION[self.microstep][0]
        self.SPR = SPR  # Steps per Revolution of the motor (360 / ??)
        self.MPR = MPR  # Milimeters per revolution of the screw
        self.MPS = (MPR / SPR) / self.microstep_int  # Millimeters per step


        self.limit_pin = limit_pin  # limit switch (pressed = LOW)
        self.DIR = DIR    # Direction GPIO Pin
        self.STEP = STEP  # Step GPIO Pin
        self.pwm_freq = pwm_freq  # PWM frequency (options are limited to a set, except for hardware PWM on pin 18)
        self.pwm_duty = pwm_duty  # PWM duty cycle
        self.accel_interval = accel_interval  # ms spent in each speed before increasing, less is more acceleration

        # Connect to pigpiod daemon
        self.pi = pigpio.pi()  # pigpio MUST BE ALREADY RUNNING with PCM clock: $ sudo pigpiod
        self.pi.wave_clear()   # clear existing waves

        # Setup limit switch pin. TODO: cambiar esto para que use pigpio
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.limit_pin, GPIO.IN)

        # Set up DIR and STEP pins as output
        self.pi.set_mode(DIR, pigpio.OUTPUT)
        self.pi.set_mode(STEP, pigpio.OUTPUT)

        # Apply microstep choice to pins
        for i in range(3):
            self.pi.write(MODE[i], self.RESOLUTION[self.microstep][1][i])

        # Set duty cycle and frequency
        self.pi.set_PWM_dutycycle(STEP, 0)              # 0 ~ Stepper Off
        self.pi.set_PWM_frequency(STEP, self.pwm_freq)  # 500 ~ 500 Hz (steps per second)

    def stepCalculation(self, displacement):
        """Convert millimeter displacement to stepper steps considering microstepping"""
        microstep = self.microstep_int  # get microstep as int, for example: 32
        step_count_float = displacement * (self.SPR / self.MPR) * microstep  # compute step counts from "mm" dsplcmnt
        step_count = floor(step_count_float)  # TODO: correct this approximation on millimeters to step rounding
        return step_count

    def displace(self,
                 displacement,
                 max_speed=10):
        """Move S axis by the specified distance in millimeters, at max speed in mm/s"""
        try:
            if displacement > 80:  # TODO: figure out why greater values make pigpio crash
                raise ValueError("".join(["PROTOCOL ERROR: displacement is greater than 80,",
                                          " this can fuck up a pigpio chain.",
                                          "\n  Doing nothing and cleaning up :("]))

            step_count = self.stepCalculation(displacement)

            # Set direction
            self.pi.write(self.DIR, step_count > 0)  # Set direction. TODO: be smarter about stepper direction
            # Create ramp for the steps
            ramp = self.generate_ramp(abs(step_count), max_speed)
            # Run the ramp
            self.run_ramp(ramp)  # Kick it!
        except LimitSwitchException as e:
            print(e)
            print("Pipetting error: something happened during stepper displacement.")
            print("  Interrupting move and advancing to limit switch safety :(")
            self.pi.wave_clear()
            sleep(1)
            self.limitRetraction()
            self.close()
        except Exception as e:
            print(e)
            print("Pipetting error: something happened during stepper displacement call.")
            print("  Doing nothing and cleaning up :(")
            self.close()

    def limitRetraction(self,
                        displacement=-10,
                        max_speed=10,
                        negative_direction=1):

        step_count = self.stepCalculation(displacement)

        # Set direction
        self.pi.write(self.DIR, negative_direction)  # Set direction. TODO: be smarter about stepper direction
        # Create ramp for the steps
        ramp = self.generate_ramp(abs(step_count), max_speed)
        # Run the ramp
        self.run_ramp(ramp, safety=True)  # Kick it!

    def run_ramp(self, ramp, safety=False):
        """
        PWM chains ramp
        https://www.raspberrypi.org/forums/viewtopic.php?p=994373
        :param safety: whether the move is for safety
        :param ramp: list of FREQUENCY-STEPS pairs lists
        :return: yo momma so fat jokes
        """

        ramp_length = len(ramp)
        wave_id = [-1] * ramp_length
        # self.pi.set_mode(self.STEP, pigpio.OUTPUT)  # Already done by __init__
        self.pi.wave_clear()  # clear existing waves

        # generate a wave per frequency
        for i in range(ramp_length):
            freq = ramp[i][0]
            micros = int(500000 / freq)
            wave_form = []
            wave_form.append(pigpio.pulse(1 << self.STEP, 0, micros))
            wave_form.append(pigpio.pulse(0, 1 << self.STEP, micros))
            self.pi.wave_add_generic(wave_form)
            wave_id[i] = self.pi.wave_create()

        # generate a chain of waves
        chain = []
        for i in range(ramp_length):
            steps = ramp[i][1]
            x = steps & 255
            y = steps >> 8
            chain += [255, 0, wave_id[i], 255, 1, x, y]

        self.pi.wave_chain(chain)      # Transmit chain.

        if not safety:
            while self.pi.wave_tx_busy():  # Sleep while transmitting and interrupt chain if limit switch is activated.
                if GPIO.input(self.limit_pin) == GPIO.LOW:
                    self.pi.wave_tx_stop()
                    raise LimitSwitchException("".join(["PROTOCOL ERROR: Limit switch activated!",
                                                        " stepper displacement cancelled prematurely."]))
                sleep(0.001)
        else:
            while self.pi.wave_tx_busy():  # Sleep while transmitting and interrupt chain if limit switch is activated.
                if GPIO.input(self.limit_pin) == GPIO.HIGH:
                    self.pi.wave_tx_stop()
                    print("Pipette moved away from limit switch.")
                sleep(0.001)

        # Cleanup
        for i in range(ramp_length):
            self.pi.wave_delete(wave_id[i])  # Delete all waves
        return True

    def generate_ramp(self, step_count, max_speed=10):
        """Generate a ramp as a list of frequency-steps pairs lists"""
        max_speed_freq = max_speed / self.MPS
        time_interval = self.accel_interval  # ms spent in each speed before increasing, less is more acceleration
        default_speeds = [10, 20, 50, 160, 320, 500, 800, 1000, 2000, 4000, 8000]
        speeds = [speed for speed in default_speeds if speed <= max_speed_freq]
        accel_steps = [ceil(time_interval * speed) for speed in speeds]

        steps_left = step_count
        next_idx = 0
        ramp = []

        if accel_steps[0]*2 >= step_count:
            return [[speeds[0], step_count]]

        for i in range(speeds.__len__()):
            ramp.append([speeds[i], accel_steps[i]])      # append at current speed and end the loop
            steps_left = steps_left - accel_steps[i] * 2  # compute how many steps are left considering accel symmetry

            next_idx = min(i+1, speeds.__len__()-1)
            if steps_left <= accel_steps[next_idx] * 2:   # if steps left wont fit in current symmetrical speed step
                break
            else:
                continue  # if the loop completes, max speed is reached, assign remaining steps to max

        ramp.append([speeds[next_idx], steps_left])

        ramp.extend(ramp[:-1][::-1])

        return ramp

    def close(self):
        self.pi.wave_clear()
        GPIO.cleanup()


stepper = SAxisPigpio()
stepper.displace(displacement=displacement, max_speed=10)
stepper.close()
