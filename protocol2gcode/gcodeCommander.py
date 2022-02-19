# Functions for sending commands to GRBL and the SAxis controller.
from pipetteDriver import Pipette
from gcodeCommander_utils import serial_reader, serial_writer, GrblError, queue_grbl_command
# from driverGcodeSender2_utils import PollThreadError
# from driverGcodeSender2_utils import GrblError
import serial as serial
import time
import threading
import queue
import socketio
import re
import sys
import pprint
from math import floor, ceil

try:
    from RPi import GPIO
except ImportError:
    print("Error: No GPIO python module found.")


class Commander(object):
    """A class for driving the Pipettin-GRBL bot v1"""

    def __init__(self,
                 protocol=None,
                 serial_device_path='/dev/ttyACM0',
                 baudrate=115200,
                 RX_BUFFER_SIZE=128,
                 serial_response_delay=0.2,
                 stepper_idle_timeout=255,
                 pipette_model="p200",
                 pipette_homing_retraction=16.8,
                 socket_port=3333,
                 sio_object=None,
                 dry=False, semi_dry=False, # TODO: use "$C" to test gcode on GRBL w/o moving the motors
                 home_pipette_at_init=False,
                 reset_bcm_pin=17,
                 interactive=False,
                 verbose=True):

        if protocol is None:
            protocol = []
        self.protocol = protocol
        self.reset_bcm_pin = reset_bcm_pin
        self.serial_response_delay = serial_response_delay
        self.stepper_idle_timeout = stepper_idle_timeout
        self.pipette_model = pipette_model
        self.pipette_homing_retraction = pipette_homing_retraction
        self.verbose = verbose
        self.dry = dry
        self.semi_dry = semi_dry
        self.interactive = interactive

        self.killed = False

        # Setup GPIO pins for Arduino reset
        if self.verbose:
            print("\ndriver message:\n    Setup GPIO pins for Arduino reset function...")
        # Broadcom pin-numbering scheme
        GPIO.setmode(GPIO.BCM)
        # Initial value low: https://raspi.tv/2013/rpi-gpio-basics-5-setting-up-and-using-outputs-with-rpi-gpio
        GPIO.setup(reset_bcm_pin, GPIO.OUT, initial=GPIO.LOW)
        # Just in case
        GPIO.output(reset_bcm_pin, GPIO.LOW)

        # Setup pipette
        self.pipette = Pipette(pipette_model=self.pipette_model, dry=self.dry, home_pipette_at_init=home_pipette_at_init, verbose=self.verbose)

        # Setup pyserial interface to GRBL
        if self.verbose:
            print("\ndriver message:\n    Connecting to" + serial_device_path + " at " + str(baudrate))
        self.serial = serial.Serial(timeout=5)  # podría ser 0 para non blocking
        self.serial.baudrate = baudrate
        self.serial.dtr = None
        self.serial.port = serial_device_path
        self.serial.open()

        # Connect to the Web GUI's websocket and initialize asynchronous listeners
        self.socket_abort = False
        self.socket_pause = False
        if sio_object is not None:
            # Use the provided socket object
            self.sio = sio_object
            # Flag use of the socket
            self.socket_use = True
        elif socket_port is not None:
            # Setup new socket
            self.sio = socketio.Client()
            self.sio.connect('http://localhost:' + str(socket_port))
            # Flag use of the socket
            self.socket_use = True
            if self.verbose:
                print("\ndriver message:\n    Using websocket")
        else:
            # Else flag socket disabled
            self.socket_use = False
            if self.verbose:
                print("\ndriver message:\n    Using dummy websocket")

        # Register socket event handlers
        if self.socket_use:
            # Register websocket event listener function for "start human intervention"
            self.sio.on('human_intervention_continue', self.continue_message_handler)
            # Register websocket event listener function for "cancelled human intervention"
            self.sio.on('human_intervention_cancelled', self.abort_message_handler)
            # Register websocket event listener function for "kill_commander"
            self.sio.on('kill_commander', self.kill_commander)

        # Threading setup
        if self.verbose:
            print("\ndriver message:\n    Setting up monitor thread events and queues...")
        # Events
        self.idle_event = threading.Event()
        self.running_event = threading.Event()
        self.alarm_event = threading.Event()
        self.unlocked_event = threading.Event()
        self.reset_event = threading.Event()
        self.report_req_event = threading.Event()
        self.gcode_unlock = threading.Event()  # used to prevent adding items to input_queue
        # Queues
        self.output_queue = queue.Queue(10000)  # GRBL messages go here
        self.ok_queue = queue.Queue(10000)  # To count OK messages from GRBL
        self.input_queue = queue.Queue(10000)  # GRBL commands go here
        self.request_queue = queue.Queue(1)  # To force one GRBL status request at a time
        self.error_queue = queue.Queue(10000)

        # Define GRBL handler threads (a writer and a monitor/message polling thread)
        self.reader_thread = threading.Thread(target=serial_reader, args=(self.serial,
                                                                          self.output_queue,
                                                                          self.input_queue, self.ok_queue,
                                                                          self.request_queue, self.error_queue,
                                                                          self.idle_event, self.running_event,
                                                                          self.alarm_event, self.unlocked_event,
                                                                          self.reset_event,
                                                                          self.sio, self.socket_use,
                                                                          self.serial_response_delay,
                                                                          self.verbose))
        self.reader_thread.daemon = False
        self.writer_thread = threading.Thread(target=serial_writer, args=(self.serial,
                                                                          self.input_queue, self.ok_queue,
                                                                          self.request_queue, self.error_queue,
                                                                          self.idle_event, self.running_event,
                                                                          self.alarm_event, self.unlocked_event,
                                                                          self.reset_event,
                                                                          self.gcode_unlock,
                                                                          self.serial_response_delay,
                                                                          self.verbose,
                                                                          RX_BUFFER_SIZE))
        self.writer_thread.daemon = False


    # Define kill signal handler
    def kill_commander(self, msg):
        """
        Handles a "kill_commander" event from the socket. Sent by "gui/lib/commander.js".
        """

        print("\ndriver message:\n    KILL: kill_commander call initiated with message: " + str(msg) + ". Current kill value: " + str(self.killed))

        # If this is the first time we are killing this
        if not self.killed:
            # Force while loop to end prematurely, skipping the rest of the protocol.
            print("\ndriver message:\n    KILL: kill_commander activated for the first time, skipping further protocol.")
            self.killed = True
        # But if this is the second time killing it
        else:
            # Then force reset the arduino immediately and exit
            self.arduino_GPIO_reset()
            raise GrblError("\ndriver message:\n    KILL: kill_commander activated for a second time, forcing hard-reset on GRBL.")


    def sio_emit(self, what, data):
        if self.socket_use:
            self.sio.emit(what, data)
        else:
            print(what)
            print(data)

    def sio_disconnect(self):
        if self.socket_use:
            if self.verbose:
                print("\ndriver message:\n    Stopping websocket")
            self.sio.disconnect()

    # Define socket handlers
    def abort_message_handler(self, msg):
        """Message handler for the "cancelled" button after human interaction pause"""
        print('Received cancel message: ', msg)
        self.socket_abort = True

    # Define socket handlers
    def continue_message_handler(self, msg):
        """Message handler for the "continue" button after human interaction pause"""
        print('Received continue message: ', msg)
        self.socket_pause = False

    def arduino_GPIO_reset(self):
        GPIO.output(self.reset_bcm_pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self.reset_bcm_pin, GPIO.LOW)
        time.sleep(1)

    def sio_emit_wpos(self, grbl_message):
        if grbl_message.upper().find('WPOS') > -1:
            wpos = re.search(r"WPos:(-?[\d\.]+),(-?[\d\.]+),(-?[\d\.]+[\|>])",
                             grbl_message, re.IGNORECASE)

            self.sio_emit('tool_data', {'position': {
                "x": wpos.group(1),
                "y": wpos.group(2),
                "z": wpos.group(3),
                "p": None  # TODO: conseguir info de la posicion de la pipeta del SAxis driver y pasarla acá
            }})

    def sio_emit_p_pos(self, pipette_position):

        if pipette_position is not None:
            pipette_position = round(pipette_position*100)/100

        self.sio_emit('tool_data', {'position': {
            "p": pipette_position
        }})

    def update_sio_wpos(self, timeout=40/1000):
        """The timeout corresponds to double the expected 20 ms response time to a status request to GRBL (plus 5 ms)."""
        if self.running_event.is_set():
            self.status(timeout)
        else:
            endtime = time.time() + timeout
            poll = True
            while poll:
                # Just in case
                self.serial.flushInput()
                self.serial.flushOutput()
                while self.serial.in_waiting:
                    discard = self.serial.readline().decode()

                # Request status report
                self.serial.write('?'.encode())  # Send "?"
                self.serial.flush()              # Wait until all data is written
                time.sleep(40/1000)              # Wait for GRBL to react to the status rquest (double the expected maximum of 20 ms).

                while self.serial.in_waiting:
                    poll_line = self.serial.readline().decode()
                    grbl_message = str(poll_line).strip()
                    # Check if the message is a status report
                    report = re.search(r"^<.+>$", grbl_message, re.IGNORECASE)
                    idle = grbl_message.lower().find("idle") > -1
                    alarm = grbl_message.upper().find("ALARM") > -1
                    error = grbl_message.upper().find("ERROR") > -1

                    # If alarm, emit and stop
                    if report and alarm:
                        if self.verbose: print("\ndriver message:\n    update_sio_wpos got an alarm state.")
                        self.sio_emit('alert', {'text': "ALARM message from GRBL: '" + re.sub("[<>]", "", grbl_message), 'type': 'alarm'})
                        while self.serial.in_waiting:
                            discard = self.serial.readline().decode()
                        poll = False

                    # If WPOS, send it to the websocket
                    elif report and idle:
                        if self.verbose: print("\ndriver message:\n    update_sio_wpos: Emitting WPOS from status: " + grbl_message)
                        self.sio_emit_wpos(grbl_message)
                        while self.serial.in_waiting:
                            discard = self.serial.readline().decode()
                        poll = False

                # Timeout check
                if endtime - time.time() <= 0.0:
                    if self.verbose: print("\ndriver message:\n    update_sio_wpos timed out.")
                    poll = False

    def fast_jog(self, fast_grbl_command, jog_feed_rate='F1000', status_tries=5):
        if self.verbose:
            print("\ndriver message:\n    Sending Jog command: " + "$J=" + fast_grbl_command + '\n')

        # Flush input buffer
        self.serial.reset_input_buffer()

        # Build command
        coord = re.search(r"([XYZ]-{0,1}[\d\.]+)", fast_grbl_command, re.IGNORECASE).group(1)
        command = "$J=G91 " + coord + ' ' + jog_feed_rate + '\n'

        # An "ok" will be received, so we must register a command in the input_queue to avoid errors.
        # It has no side effects, the jog commands are ignored by the serial_writer.
        self.input_queue.put(command)

        # Send Jog command
        self.serial.write(str.encode(command))

        # Wait until all data is written
        if self.verbose:
            print("\ndriver message:\n    Waiting until all data is written. Flushing...")
        self.serial.flush()

        # Wait for "ok" from serial_reader
        if self.verbose:
            print("\ndriver message:\n    Waiting for input_queue join...")
        self.wait_for_input_queue_join(sleepy_time=0)
        
        # To avoid the character counting error in serial_writer,
        # get the 'ok' queue item and mark it done:
        self.ok_queue.get()
        self.ok_queue.task_done()

    def wake_grbl(self):
        if self.verbose:
            print("\ndriver message:\n    Waking GRBL...")

        # Wake up GRBL
        self.serial.write(str.encode("\r\n\r\n"))
        # Wait for grbl to initialize  # TODO: improve logic, sleep is unreliable...
        time.sleep(2)

        if self.verbose:
            print("\ndriver message:\n    Resetting input buffer...")

        self.serial.reset_input_buffer()  # Flush startup text in serial input

        # Just in case
        # See: https://github.com/michaelfranzl/gerbil/blob/e6828fd5a682ec36970de83d38a0bea46b765d8d/interface.py#L69
        self.serial.flushInput()
        self.serial.flushOutput()

    def status(self, timeout=None, raise_error=False):
        """
        Report utility function.

        See: https://github.com/gnea/grbl/wiki/Grbl-v1.1-Interface#real-time-status-reports
        """
        
        if self.verbose and self.request_queue.unfinished_tasks > 0:
            print("\ndriver message:\n    status() Warning: the request_queue has pending status requests: " + str(self.request_queue.unfinished_tasks))

        # Get the one queue item, thereby blocking other requests, and/or wait until other requests are done.    
        self.request_queue.get()
        self.serial.write('?'.encode())  # Send "?"

        timed_out = False

        if timeout is None:
            # Wait for task_done in serial_reader to update
            self.request_queue.join()
        else:
            endtime = time.time() + timeout
            # Wait for task_done in serial_reader to update.
            while self.request_queue.unfinished_tasks > 0:
                if endtime - time.time() <= 0.0:
                    if raise_error:
                        raise GrblError("\ndriver message:\n    ERROR: status() timed out waiting for status report.")
                    else:
                        print("\ndriver message:\n    status(): Timed out waiting for status report.")
                        timed_out = True
                        break
                time.sleep(self.serial_response_delay)

        # Flag updated events
        if timed_out:
            idle, alarm = None, None
        else:
            idle = self.idle_event.is_set()
            alarm = self.alarm_event.is_set()

        # Put back the item, releasing status requests in other functions.
        self.request_queue.put("idle")

        return idle, alarm

    def wait_for_idle(self, timeout=None, raise_error=False):
        """Report utility function"""

        idle, alarm = self.status(timeout=self.serial_response_delay,
                                  raise_error=False)

        if timeout is None:
            if self.verbose:
                print("\ndriver message:\n    Waiting for idle (no time out).")
            while not idle:
                idle, alarm = self.status(timeout=self.serial_response_delay,
                                          raise_error=False)
                if alarm:
                    print("\ndriver message:\n    Alarm fired while waiting for idle: " + str(timeout))
                    if raise_error:
                        raise GrblError("\ndriver message:\n    ERROR: alarm while waiting for idle status report.")
                    break
        else:
            if self.verbose:
                print("\ndriver message:\n    Waiting for idle with timeout: " + str(timeout))
            endtime = time.time() + timeout
            while not idle:
                idle, alarm = self.status(timeout=self.serial_response_delay,
                                          raise_error=False)
                if endtime - time.time() <= 0.0:
                    print("\ndriver message:\n    ERROR: timed out waiting for status report.")
                    if raise_error:
                        raise GrblError("\ndriver message:\n    ERROR: timed out waiting for status report.")
                    else:
                        break

        return idle, alarm

    def wait_for_input_queue_join(self, sleepy_time=1):
        """Wait for an empty input_queue (no grbl commands in queue). Does not imply IDLE state."""
        # Sleep some time just in case
        time.sleep(sleepy_time)

        if self.verbose:
            print("\ndriver message:\n    waiting for empty input_queue (wait_for_input_queue_join call).")

        # While the input_queue is still being processed (not enough get() calls yet),
        # and while the tasks have not been marked as done (by an "ok" response)
        # sleep...
        while not self.input_queue.empty() or self.input_queue.unfinished_tasks > 0:
            # Request a status
            self.status(timeout=1, raise_error=False)

            # Check if alarms were set
            if self.alarm_event.is_set():
                raise GrblError("\ndriver message:\n    alarm event raise while waiting for input_queue join")
            time.sleep(self.serial_response_delay)

    def start_threads(self):
        # Initial state of events and queues
        self.alarm_event.clear()
        self.idle_event.clear()
        self.gcode_unlock.clear()
        self.unlocked_event.set()
        self.reset_event.clear()
        self.report_req_event.set()
        self.request_queue.put("init")  # Prime the report request queue
        # Start the GRBL handler threads
        if self.verbose:
            print("\ndriver message:\n    Starting threads...")
        self.reader_thread.start(), self.writer_thread.start()  # call the thread functions
        if self.verbose:
            print("\ndriver message:\n    Setting thread run event...")
        self.running_event.set()  # release the "wait" on the thread functions

    def check_grbl_status(self):
        # Update status report
        print("\ndriver message:\n    Waiting for status report 1...")
        idle, alarm = self.wait_for_idle(timeout=3)

        if idle and not alarm:
            return True

        if alarm:
            # Try resetting the arduino
            print("\ndriver message:\n    Hard-resetting arduino...")
            self.arduino_GPIO_reset()

        print("\ndriver message:\n    Waiting for status report 2...")
        idle, alarm = self.wait_for_idle(timeout=3)

        if idle and not alarm:
            return True

        # Si esta bloqueado, pero tampoco se requiere reset,
        # significa que leimos el mensaje de "$X for unlock" (ver serial_reader).
        if not self.unlocked_event.is_set() and not self.reset_event.is_set():
            print("\ndriver message:\n    GRBL Alarm/Error, trying to unlock with $X...")

            # Send unlock code to GRBL input_queue.
            # Since its a setting line, it will wait/block for an "ok".
            queue_grbl_command("$X", self.input_queue, self.gcode_unlock, verbose=self.verbose)

            # Wait for idle
            print("\ndriver message:\n    Waiting for idle GRBL report 3...")
            idle, alarm = self.wait_for_idle(timeout=2)

        if idle and not alarm:
            return True
        else:
            raise GrblError("\ndriver message:\n    ERROR: GRBL couldnt be set to IDLE.")

    def steppers_on(self):
        # Set the stepper idle timeout in GRBL (enable steppers if 255)
        if self.stepper_idle_timeout is not None:
            assert isinstance(self.stepper_idle_timeout, int) and 0 <= self.stepper_idle_timeout <= 255
            # input_queue.put("$1=" + str(stepper_idle_timeout) + "\n")
            queue_grbl_command("$1=" + str(self.stepper_idle_timeout) + "\n",
                               self.input_queue, self.gcode_unlock, verbose=self.verbose)
            time.sleep(self.serial_response_delay)

        return self.stepper_idle_timeout

    def steppers_off(self):
        print("\ndriver message:\n    Disabling steppers...")
        queue_grbl_command("$1=20",
                           self.input_queue, self.gcode_unlock, verbose=self.verbose)
        queue_grbl_command("G91 G1 Z-0.01 F1000", 
                           self.input_queue, self.gcode_unlock, verbose=self.verbose)

    def run_protocol(self,
                     wait_prefix="Wait",
                     human_intervention_prefix="HUMAN",
                     s_axis_home_prefix="Phome;",
                     s_axis_displacement_prefix="Pmove;",
                     s_axis_eject_prefix="Peject;"
                     ):
        try:
            print("\ndriver message:\n    Starting protocol!")

            self.wake_grbl()

            if not self.running_event.is_set(): self.start_threads()

            self.check_grbl_status()

            self.steppers_on()

            # Run protocol
            # Setup protocol line counter
            i = 0

            # Iterate over protocol lines
            while i < self.protocol.__len__() and not self.killed:

                # Get a new protocol line
                line = self.protocol[i]

                # Wait for a bit, in case something did not yet register
                time.sleep(self.serial_response_delay)

                # Print protocol step
                if self.verbose:
                    print("\ndriver message:\n    Protocol step {} of {}".format(i + 1, self.protocol.__len__()))
                    print("\ndriver message:\n    Now parsing command:\n {protocol}".format(protocol=self.protocol[i]))

                # Check for errors in threads, and stop if any are found.
                if not self.error_queue.empty():
                    while not self.error_queue.empty():
                        error = self.error_queue.get()
                        print("\ndriver message:\n    Errors detected by the threading functions: " + error)
                    raise GrblError("Alert during protocol streaming: errors detected by the threading functions.")

                # Check for alarms or errors from GRBL
                idle, alarm = self.status()
                if alarm:
                    raise GrblError("Alert during protocol streaming: GRBL's sent an alarm or error message.")

                # # Interactive mode ####
                # # Offer a rudimentary menu if interactive mode is enabled, useful for debugging.
                # if interactive:
                #     print(
                #         "\ndriver message:\n    " +
                #         "Enter single command and press enter (gcode, q: quit, n: next, s: skip).")
                #     line = input(" > ")
                #
                #     if line == "?":
                #         self.serial.write(str.encode("?"))
                #         time.sleep(0.2)  # TODO: improve logic, sleep is unreliable...
                #         continue
                #
                #     # Skip a line from the protocol
                #     elif line == "s":
                #         if i == self.protocol.__len__() - 1:
                #             i = 0
                #             input("Reached end of protocol. Press enter to start over...")
                #         else:
                #             print("\ndriver message:\n    Skipping line {}: {}".format(i, self.protocol[i]))
                #             i += 1
                #         continue
                #
                #     # Quit
                #     elif line == "q":
                #         print("Terminating interactive session...")
                #         break
                #
                #     # Send next line from the protocol
                #     elif line == "n" or line == "":
                #         if i == self.protocol.__len__() - 1:
                #             input("Reached end of protocol, press enter to start over...")
                #             i = 0
                #             continue
                #         else:
                #             line = self.protocol[i]
                #             print("\ndriver message:\n    Sending protocol line: {}".format(line))
                #             # i += 1
                #
                #     # Send the input to GRBL
                #     else:
                #         # Decrement the line index here,
                #         # as it will be undesirably incremented
                #         # at the end of the loop
                #         i -= 1

                # Process commands ####

                # First, wait for gcode block release (by the serial_writer) if any.
                # # It can only come from having sent homing or setting commands.
                # # This line is necessary because "idle_event.wait()" was not enough, the issue being
                # # that "idle_event" could be mistakenly set during a short period after sending a $H command,
                # # because there is a lag between serial.write and a non-idle status request response.
                # # This leads to "leaky" execution of the next protocol line
                # # (xej: the line that followed homing command).
                while not self.gcode_unlock.is_set():
                    time.sleep(self.serial_response_delay)
                    if self.alarm_event.is_set():  # Just in case
                        raise GrblError("GRBL Alarm/Error while waiting for gcode_unlock event.")
                # # Note: upon a setting line, the serial_writer ends up waiting for:
                # # input_queue.join()  # gather "ok"s
                # # idle_event.wait()   # ensure idle state

                # Still, the same could happen when a "move" gcode is sent, resulting in the same problem,
                # # even though we are waiting for "idle_event" to be set.
                # # A solution would be to lock "tools" (non GRBL commands) until all "ok"s are collected
                # # and GRBL reports IDLE. That is marked by a "joined" input_queue, therefore:
                # input_queue.join()
                # # But this must be checked in each tool's "if" clause.
                # # I do not use "gcode_unlock.wait()" because updating that one depends on sending
                # # gcode with input_queue.put(), while input_queue.join() only depends on the serial_reader.

                # Skip everything if dry mode is on
                if self.dry:
                    if self.verbose:
                        print("\ndriver message:\n    dry mode; skipping line: " + str(i) + line)
                    print(i, line)
                    i += 1
                    continue
                # Skip protocol comments
                if line.startswith(";"):
                    if self.verbose:
                        print("\ndriver message:\n    skipping comment line: " + str(i) + line)
                    i += 1
                    continue
                # Skip homing if semi_dry mode
                elif line.strip().startswith("$H") and self.semi_dry:
                    pass  # Move on

                # Wait action
                elif line.startswith(wait_prefix):
                    self.wait(line)
                # Human action
                elif line.startswith(human_intervention_prefix):
                    self.human(line, i)
                # Pipette home action
                elif line.startswith(s_axis_home_prefix):
                    self.pipette_home(line, i)
                # Pipette move actions
                elif line.startswith(s_axis_displacement_prefix):
                    self.pipette_displace(line, i)
                # Pipette move actions
                elif line.startswith(s_axis_eject_prefix):
                    self.tip_eject(line, i)
                # Else, stream GRBL/GCODE actions to GRBL:
                else:
                    self.send_gcode(line, i)


                # Go get another line from the protocol list object...
                i += 1

        except GrblError as e:
            print("\ndriver message:\n    GRBL error exception called during protocol streaming:\n    ", e)
            exit_code = 1
        else:
            print("\ndriver message:\n    Protocol run ended.")
            exit_code = 0
        
        # Done in commander.py
        #finally:
        #    self.cleanup()

        return exit_code

    def send_gcode(self, line, i=None):
        # If a setting line, subsequent protocol parsing must be blocked.
        # # The blockade is eventually released by the "serial_writer" thread.
        if line.strip().startswith("$"):
            self.gcode_unlock.clear()
        # Send command
        queue_grbl_command(line,
                           self.input_queue,
                           self.gcode_unlock,
                           verbose=self.verbose)

    def send_to_serial(self, command):
        # Strip comments/spaces/new line and capitalize. Note: los comentarios son cosas entre paréntesis.
        command = re.sub(r'\s|\(.*?\)', '', command).upper()
        self.serial.write(str.encode(command + '\n'))  # Send command to serial directly
        self.serial.flush()                            # Wait until all data is written

    def wait(self, line, i=None):
        # Wait for IDLE message from GRBL
        self.wait_for_input_queue_join()
        self.wait_for_idle(raise_error=True)

        seconds = float(line.split(";")[1])
        if self.verbose:
            print("\ndriver message:\n    Waiting for " + str(seconds) + " seconds.\n")
        time.sleep(seconds)  # TODO: improve logic, sleep is unreliable...

        if self.verbose:
            print("\ndriver message:\n    Done waiting for " + str(seconds) + " seconds.\n")

    def human(self, line, i):
        # Wait for IDLE message from GRBL
        self.wait_for_input_queue_join()
        self.wait_for_idle(raise_error=True)

        socket_pause = True
        message = str(line.split(";")[1])
        if self.verbose:
            print("\ndriver message:\n    Waiting for HUMAN with message: " + message)
        if self.socket_use:
            self.sio_emit('human_intervention_required', {'text': message})
            while socket_pause and not self.alarm_event.is_set() and not self.killed:
                if self.verbose:
                    print("\ndriver message:\n    Waiting for websockets...")
                time.sleep(1)  # TODO: improve logic, sleep is unreliable...
                if self.socket_abort:
                    raise GrblError(
                        "Abort human action! Intervention cancelled on command " + str(i) + ": " + line)

    def pipette_home(self, line=None, i=None):
        if self.verbose:
            print("\ndriver message:\n    Homing pipette (after GRBL idle)...")
        # Wait for IDLE message from GRBL
        self.wait_for_input_queue_join()
        self.wait_for_idle(raise_error=True)
        if line is not None:
            millimeters = float(line.split(";")[1])
        else:
            millimeters = self.pipette_homing_retraction
        self.pipette.limitRetraction(retraction_displacement=millimeters)
        if self.verbose:
            print("\ndriver message:\n    Pipette homing done! for command: " + str(i))

        # Update pipette position
        self.sio_emit_p_pos(self.pipette.pipette["current_volume"])


    def pipette_displace(self, line="Pmove;0", i=None):
        if self.verbose:
            print("\ndriver message:\n    Pipetting displacement (after GRBL idle)...")
        
        # Wait for all "ok"s
        self.wait_for_input_queue_join()

        # Wait for IDLE message from GRBL: THREE TIMES
        [self.wait_for_idle(raise_error=True) for i in range(3)]

        # Get millimeters
        millimeters = float(line.split(";")[1])

        # Displace pipette
        self.pipette.displace(displacement=millimeters)
        if self.verbose:
            print("\ndriver message:\n    Pipetting done!" + str(millimeters) + " mm, for command: " + str(i))

        # Update pipette position
        self.sio_emit_p_pos(self.pipette.pipette["current_volume"])

    # def pipette_displace_volume(self, microliters=0, i=None):
    #     if self.verbose:
    #         print("\ndriver message:\n    Pipetting displacement (after GRBL idle)...")
        
    #     # Wait for all "ok"s
    #     self.wait_for_input_queue_join()

    #     # Wait for IDLE message from GRBL: THREE TIMES
    #     [self.wait_for_idle(raise_error=True) for i in range(3)]

    #     # Displace pipette
    #     self.pipette.displace(displacement=microliters)

    #     if self.verbose:
    #         print("\ndriver message:\n    Pipetting done! for command: " + str(i))

    #     # Update pipette position
    #     self.sio_emit_p_pos(self.pipette.pipette["current_volume"])

    def tip_eject(self, line=None, i=None):
        if self.verbose:
            print("\ndriver message:\n    Ejecting tip (after GRBL idle)...")

        # Wait for IDLE message from GRBL
        self.wait_for_input_queue_join()

        # Wait for IDLE message from GRBL: THREE TIMES
        [self.wait_for_idle(raise_error=True) for i in range(3)]

        # Eject tip with servo
        self.pipette.eject()

        if self.verbose:
            print("\ndriver message:\n    Tip ejected! with command: " + str(i))

    def cleanup(self):
        print("\ndriver message:\n    Cleaning up!")
        # Just in case
        self.serial.flushInput()
        self.serial.flushOutput()

        # If the threads were setup:
        if self.running_event.is_set():

            # Disable steppers before quitting.
            print("\ndriver message:\n    Disabling steppers...")
            self.steppers_off()

            # Stop the threads
            print("\ndriver message:\n    Stop GRBL threading monitors")
            self.running_event.clear()

        # Cleanup serial interface
        print("\ndriver message:\n    Close serial connection")
        self.serial.close()

        # Close socket
        print("\ndriver message:\n    Disconnecting websocket...\n")
        self.sio_disconnect()

        # Cleanup pipette and  GPIOs
        print("\ndriver message:\n    Cleanup pigpio and GPIO")
        self.pipette.close()  # Includes GPIO cleanup

        print("\ndriver message:\n    Done cleaning up. Have a nice day! :)\n")
