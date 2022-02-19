from time import sleep
from math import ceil, floor, pi

try:
    from RPi import GPIO
except ImportError:
    print("Dummy GPIO")
    from dummyGPIO import GPIO

try:
    import pigpio as pigpio
except ImportError:
    print("Dummy pigpio")
    from dummyGPIO import pigpio

class LimitSwitchException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'Exception message: {0} '.format(self.message)
        else:
            return 'LimitSwitchException has been raised!'


class Pipette(object):
    def __init__(self, pipette_model=None,
                 dry=False,
                 home_pipette_at_init=True,
                 microstep="1/32", delay_default=0.0208,
                 SPR=200, MPR=8,
                 MODE=(25, 8, 7),  # MODE=(14, 15, 18)
                 limit_pin=14, DIR=20, STEP=16,
                 SERVO=23,
                 pwm_freq=500, pwm_duty=128, accel_interval=0.5*80/1000,
                 verbose=False):
        """
        Setting 'pipette' to one of the available options will scale the shaft's displacement
        in such a way that the input 'displacement' is interpreted as pipette volume units.

        By default pipette=None, and the displacement is interpreted as 'linear' (in millimeter units) with pipette_scaler=1.
        """

        if not dry:
            if verbose: print("\nSAxisPigpio:\n    Pipette axis init")
        else:
            if verbose: print("\nSAxisPigpio:\n    Pipette axis init (dry run)")

        self.pipettes = {
            "syringe_3mL": {
                "vol_max": 3000,  # microliters
                "scaler":    20     # microliters / millimeter
            },
            "syringe_1mL": {
                "vol_max": 1000,  # microliters
                "scaler": 20        # microliters / millimeter
            },
            "p1000": {
                "vol_max": 1000,  # microliters
                "scaler": 20        # microliters / millimeter
            },
            "p200": {
                "vol_max": 200-10,                      # [microliters] maximum pipette volume (as indicated by dial) with some tolerance subtracted.
                "scaler": pi*((4/2)**2),                # [microliters/millimeter] conversion factor, from mm (shaft displacement) to uL (corresponding volume).
                "tipLength": 50,                        # [millimeters] total length of the pipette's tip.
                "tipSealDistance": 6,                   # [millimeters] distance the pipette must enter the tip to properly place it.
                # "homing_backslash_compensation": 20.0,  # not used
                "backslash_compensation_volume": 0.1,   # [microliters] extra move before poring volume, corresponds to backslash error after drawing (only applies after a direction change).
                "extra_draw_volume": 8,                 # [microliters] extra volume that the pipette needs to draw (to avoid the "under-drawing" problem). See: calibration/data/21-08-17-p200-balanza_robada/README.md
                "back_pour_correction": 4,              # [microliters] volume that is returned to the source tube after pipetting into a new tip (a sort of backslash correction).
                "current_volume": None
            },
            "p20": {
                "vol_max": 19,  # microliters
                "scaler": pi*((4/2)**2)        # microliters / millimeter
            },
            "none" :{
                "vol_max": 10,                          # [microliters] maximum pipette volume (as indicated by dial) with some tolerance subtracted.
                "scaler": 1,                            # [microliters/millimeter] conversion factor, from mm (shaft displacement) to uL (corresponding volume).
                "tipSealDistance": 1,                   # [millimeters] distance the pipette must enter the tip to properly place it.
                "backslash_compensation_volume": 1,     # [microliters] extra move before poring volume, corresponds to backslash error after drawing (only applies after a direction change).
                "extra_draw_volume": 1,                 # [microliters] extra volume that the pipette needs to draw (to avoid the "under-drawing" problem). See: calibration/data/21-08-17-p200-balanza_robada/README.md
                "current_volume": None
            }
        }                  # available micropipette models and characteristics

        if pipette_model is None:
            self.pipette_scaler = 1
            self.pipette = self.pipettes["none"]
        else:
            self.pipette = self.pipettes[pipette_model]
            self.pipette_scaler = self.pipette["scaler"]

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
        self.MPR = MPR  # Millimeters per revolution of the screw
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

        # Register servo, off state
        self.SERVO = SERVO
        self.pi.set_servo_pulsewidth(self.SERVO, 0)     # off
        #pi.set_servo_pulsewidth(SERVO, 500)   # min
        #pi.set_servo_pulsewidth(SERVO, 2500)  # max

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

        self.dry = dry
        if home_pipette_at_init:
            if verbose: print("\nSAxisPigpio:\n    Pipette axis homing init.")
            self.limitRetraction()

        if verbose: print("\nSAxisPigpio:\n    Pipette axis ready!")

    def stepCalculation(self, displacement, verbose=False):
        """
        Convert millimeter displacement to stepper steps considering microstepping.
        Positive displacements load volume.
        Negative displacements eject volume.
        """
        microstep = self.microstep_int  # get microstep as int, for example: 32
        step_count_float = displacement * (self.SPR / self.MPR) * microstep  # compute step count from "mm" displacement
        step_count = floor(step_count_float)  # TODO: correct this approximation on millimeters to step rounding
        return step_count

    def eject(self, wait_time=1, eject_moves=[500,2500], verbose=False):
        # Library pulse width limitation: 500-2500 ms
        # http://abyz.me.uk/rpi/pigpio/python.html#set_servo_pulsewidth
        # Tower-pro MG995 servo typical PW: 500 ms (0deg) to 2500 ms (180 deg)
        # https://components101.com/motors/mg995-servo-motor
        self.pi.set_servo_pulsewidth(self.SERVO, eject_moves[1])  # eject
        sleep(wait_time)

        self.pi.set_servo_pulsewidth(self.SERVO, eject_moves[0])  # retract
        sleep(wait_time)

        self.pi.set_servo_pulsewidth(self.SERVO, 0)    # off

    def displace(self,
                 displacement,
                 max_speed=10, verbose=False):
        """
        Move S axis by the specified volume, at max speed in mm/s.
        :param displacement: volume in microliters. Positive displacements load volume. Negative displacements eject volume.
        """
        
        displacement_mm = float(displacement) / self.pipette_scaler

        if self.dry:
            if self.verbose: print("\nSAxisPigpio:\n    //// Dry run, not displacing pipette axis by: ", str(displacement_mm))
        else:
            try:
                if abs(displacement_mm) > 80:  # TODO: figure out why greater values make pigpio crash
                    raise ValueError("".join(["PROTOCOL ERROR: displacement_mm is greater than 80,",
                                              " this can fuck up a pigpio chain.",
                                              "\n  Doing nothing and cleaning up :("]))

                step_count = self.stepCalculation(displacement_mm)
                if verbose: print("\nSAxisPigpio:\n    //// displacement_mm is {}, step count is {}, direction is {}.".format(
                    displacement_mm,
                    step_count,
                    step_count < 0))

                # Set direction
                self.pi.write(self.DIR, step_count < 0)  # Set direction. TODO: be smarter about stepper direction
                # Create ramp for the steps
                ramp = self.generate_ramp(abs(step_count), max_speed)
                # Run the ramp
                self.run_ramp(ramp)  # Kick it!

                # Register new volume
                if self.pipette["current_volume"] is not None:
                    # reverses s_axis_movement calculation in gcodeBuilder.py to volume units
                    self.pipette["current_volume"] += displacement * self.pipette["scaler"]


            except LimitSwitchException as e:
                print(e)
                print("\nSAxisPigpio:\n    //// Pipetting error: something happened during stepper displacement.")
                print("\nSAxisPigpio:\n    ////   Interrupting move and advancing to limit switch safety :(")
                self.pi.wave_clear()
                sleep(1)
                self.limitRetraction()
                self.close()
                raise LimitSwitchException("//// Limit switch activated during displacement.")

            except Exception as e:
                print(e)
                print("\nSAxisPigpio:\n    //// Pipetting error: something happened during stepper displacement call.")
                print("\nSAxisPigpio:\n    ////   Doing nothing and cleaning up :(")
                self.close()
                raise Exception("//// Error during displacement")

    def limitRetraction(self,
                        raise_displacement=25,      # Upward movements occur in segments this long (pigpio ramps cant be infinite).
                        retraction_displacement=2,  # Downward movement after triggering the limit switch.
                        max_speed=5,
                        limit_switch_direction=0,
                         verbose=False):
        """Retract S axis up to limit switch and move down."""
        if self.dry:
            if verbose: print("\nSAxisPigpio:\n    Dry run, not homing pipette axis.")
        else:
            # Count steps
            step_count = self.stepCalculation(raise_displacement)
            # Set direction
            self.pi.write(self.DIR, limit_switch_direction)  # Set direction. TODO: be smarter about stepper direction
            # Create ramp for the steps
            ramp = self.generate_ramp(abs(step_count), max_speed)
            # Run the ramp
            while GPIO.input(self.limit_pin) == GPIO.HIGH:
                self.run_ramp(ramp, safety_raise=True)  # Kick it!
            if verbose: print("\nSAxisPigpio:\n    Pipette moved up to limit switch.")

            # Retract
            if verbose: print("\nSAxisPigpio:\n    Now retracting by {displacement} mm".format(displacement=1))
            step_count = self.stepCalculation(1)
            self.pi.write(self.DIR, not limit_switch_direction)
            ramp = self.generate_ramp(abs(step_count), max_speed)
            while GPIO.input(self.limit_pin) == GPIO.LOW:
                # While the pipette is activating the sensor
                self.run_ramp(ramp, safety_lower=True)
            if verbose: print("\nSAxisPigpio:\n    Pipette just under the limit switch.")

            # Extra retraction
            step_count = self.stepCalculation(retraction_displacement)
            self.pi.write(self.DIR, not limit_switch_direction)
            ramp = self.generate_ramp(abs(step_count), max_speed)
            self.run_ramp(ramp, safety_lower=True)
            if verbose: print("\nSAxisPigpio:\n    Extra retraction by {displacement} mm".format(displacement=retraction_displacement))

            # Register home position
            self.pipette["current_volume"] = 0

    def run_ramp(self, ramp, safety_raise=False, safety_lower=False, verbose=False):
        """
        Process a ramp into a PWM chain, and transmit it.
        https://www.raspberrypi.org/forums/viewtopic.php?p=994373
        :param safety_raise: whether the move is for safety raising
        :param safety_lower: whether the move is for safety lowering
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

        # Limit switch check
        if GPIO.input(self.limit_pin) == GPIO.LOW and not (safety_raise or safety_lower):
            raise LimitSwitchException("".join(["PROTOCOL ERROR: Limit switch is active!",
                                                " stepper was not moved."]))
        else:
            self.pi.wave_chain(chain)      # Transmit chain.

        if safety_raise:
            while self.pi.wave_tx_busy():
                # Sleep while transmitting OR interrupt chain if limit switch is activated.
                if GPIO.input(self.limit_pin) == GPIO.LOW:
                    self.pi.wave_tx_stop()
                sleep(0.1)
        elif safety_lower:
            # Sleep while transmitting OR interrupt chain if limit switch is released.
            while self.pi.wave_tx_busy():
                sleep(0.1)
                continue
        else:
            # Sleep while transmitting and interrupt chain if limit switch is activated.
            while self.pi.wave_tx_busy():
                if GPIO.input(self.limit_pin) == GPIO.LOW:
                    self.pi.wave_tx_stop()
                    self.pi.wave_clear()
                    GPIO.cleanup()
                    raise LimitSwitchException("".join(["PROTOCOL ERROR: Limit switch activated!",
                                                        " stepper displacement cancelled prematurely.",
                                                        " Cleaning up and closing."]))
                sleep(0.01)

        # Cleanup
        for i in range(ramp_length):
            self.pi.wave_delete(wave_id[i])  # Delete all waves
        return True

    def generate_ramp(self, step_count, max_speed=10, verbose=False):
        """
        Generate a ramp as a list of frequency-steps pairs lists

        step_count = 200
        ramp = generate_ramp(step_count)
        print(step_count)
        print(ramp)
        print(sum(i[1] for i in ramp))

        for s in [123,465,98,231,99789]:
            ramp = generate_ramp(s)
            print(sum(i[1] for i in ramp) == s)
        """
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
        self.pi.stop()
        GPIO.cleanup()
