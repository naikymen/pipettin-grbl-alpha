import time
import re
from grbl_error_codes import get_error_by_code
from grbl_alarm_codes import get_alarm_by_code


class GrblError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'GRBL error: the machine needs to be reset: {0} '.format(self.message)
        else:
            return 'GRBL error has been raised!'


class PollThreadError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'Polling thread error: {0} '.format(self.message)
        else:
            return 'PollThreadError has been raised!'


def serial_reader(serial_interface,
                  output_queue, input_queue, ok_queue, request_queue, error_queue,
                  idle_event, running_event, alarm_event, unlocked_event, reset_event,
                  sio, socket_use,
                  serial_response_delay=0.1,
                  verbose=False):
    # Wait for polling request by "running_event.wait()"
    print('\nserial_reader:\n    waiting for running_event...')
    running_event.wait()

    print('\nserial_reader:\n    running_event is set! polling serial_interface continuously...')
    try:
        while running_event.is_set():
            # Receive lines from serial_interface and put them in the output queue
            if serial_interface.in_waiting:
                # Wait for grbl response with carriage return
                # Although a bit unnecessary: the while loop condition
                # ensures that there will always be a message for us at this point
                # if verbose: print('\nserial_reader:\n    new serial messages, reading from pyserial...')
                poll_line = serial_interface.readline().decode()  # Maybe use "read_until()", aunque quizas da igual.
                grbl_message = str(poll_line).strip()
                # if verbose: print('\nserial_reader:\n    processing received message: ' + grbl_message)

                # Check if the message is the output of GRBL configuration (i.e. the response to '$$')
                setting = re.search(r"^\$(\d+)=(.*)$", grbl_message, re.IGNORECASE)
                # Check if the message is a status report
                report = re.search(r"^<.+>$", grbl_message, re.IGNORECASE)

                # If a setting, print it and continue
                if setting is not None:
                    if verbose:
                        print('\nserial_reader:\n    setting line received: ' + grbl_message)
                    continue
                else:
                    print('\nserial_reader:\n    non-setting line received: ' + grbl_message)

                # Place the message in the output queue
                output_queue.put(grbl_message)  # Useless for now

                # If WPOS, send it to the websocket
                if grbl_message.upper().find('WPOS') > -1 and report:
                    wpos = re.search(r"WPos:(-?[\d\.]+),(-?[\d\.]+),(-?[\d\.]+[\|>])",
                                     grbl_message, re.IGNORECASE)
                    if socket_use:
                        sio.emit('tool_data', {'position': {
                            "x": wpos.group(1),
                            "y": wpos.group(2),
                            "z": wpos.group(3),
                            "p": None  # TODO: conseguir info de la posicion de la pipeta del SAxis driver y pasarla acá
                        }})

                # If Bf, register its values (requires $10=2)
                if grbl_message.upper().find('BF') > -1 and report:
                    buffer_status = re.search(r"Bf:(-?[\d\.]+),(-?[\d\.]+)[\|>]", grbl_message, re.IGNORECASE)
                    ok_planner_buffer_blocks = 15 == buffer_status.group(1)
                    ok_bytes_rx_buffer = 127 == buffer_status.group(2)

                # If ALARM
                if grbl_message.upper().find("ALARM") > -1:
                    alarm_code = re.search(r"ALARM.(\d{1,2})", grbl_message, re.IGNORECASE)
                    if alarm_code is not None:
                        alarm_code = alarm_code.group(1)
                    else:
                        alarm_code = -1
                    print('\nserial_reader:\n    ALARM line received: ' + grbl_message +
                          " Description: " + get_alarm_by_code(alarm_code))

                    # Put the error in the queue
                    error_queue.put(get_error_by_code(alarm_code))
                    # Emit a socket alert
                    if socket_use:
                        sio.emit('alert', {'text': "ALARM message from GRBL: '" +
                                                   re.sub("[<>]", "", grbl_message) +
                                                   "'. and alarm code: " + str(alarm_code), 'type': 'alarm'})
                    # Sound the alarm
                    alarm_event.set()

                # If ERROR
                elif grbl_message.upper().find("ERROR") > -1:
                    error_code = re.search(r"ERROR.(\d{1,2})", grbl_message, re.IGNORECASE)
                    if error_code is not None:
                        error_code = error_code.group(1)
                    else:
                        error_code = -1
                    print('\nserial_reader:\n    ERROR line received: ' + grbl_message +
                          " Description: " + get_error_by_code(error_code))

                    # Put the error in the queue
                    error_queue.put(get_error_by_code(error_code))
                    # Emit a socket alert
                    if socket_use:
                        sio.emit('alert', {'text': "ERROR message from GRBL: " + re.sub("[<>]", "", grbl_message),
                                           'type': 'error'})
                    # Sound the alarm
                    alarm_event.set()  # TODO: handle non-locking errors differently from alarms

                # If OK
                elif grbl_message.lower().find("ok") > -1:
                    ok_queue.put(grbl_message)  # Count "ok" responses
                    input_queue.task_done()  # Mark a GRBL command as "done"
                    if verbose:
                        print('\nserial_reader:\n    OK received, remaining tasks: ' +
                              str(input_queue.unfinished_tasks))

                # If IDLE
                elif grbl_message.lower().find("idle") > -1 and report:
                    if verbose:
                        print('\nserial_reader:' +
                              '\n    Line received, status report "idle": ' + grbl_message +
                              "\n    Unfinished tasks: " + str(input_queue.unfinished_tasks)
                              )
                    alarm_event.clear()

                    # Solo setear "idle" cuando el buffer esta realmente en cero
                    # $10=2
                    #  Enabled Buf: field appears with "planner" and "serial RX" available buffer.
                    #  This shows the number of blocks or bytes **available** in the respective buffers.
                    #  Ejemplo: Bf:7,128
                    #  https://github.com/grbl/grbl/issues/932#issuecomment-198737235

                    # rx_planner = re.search(r"<.*Bf\:(\d+),(\d+).*>", grbl_message, re.IGNORECASE).group(2)
                    # buf_planner = re.search(r"<.*Bf\:(\d+),(\d+).*>", grbl_message, re.IGNORECASE).group(1)
                    # if verbose: print('\nserial_reader:\n' +
                    # '    Planner buffer: ' + buf_planner + " RX buffer: " + rx_planner)

                    # There are 15 planner blocks, and 128 buffer bytes,
                    # which must all be available in order to be _truly_ IDLE.
                    # if int(buf_planner) == 15 and int(rx_planner) == 128:
                    #    idle_event.set()
                    # else:
                    #    idle_event.clear()

                    idle_event.set()

                # If HOMING
                elif grbl_message.lower().find("home") > -1 and report:
                    if verbose:
                        print('\nserial_reader:\n    Line received, status report "Home": ' + grbl_message)
                    idle_event.clear()  # Porque GRBL no está IDLE durante el homing.
                    alarm_event.clear()  # Porque home significa que no hay alarma.

                # If RUNNING
                elif grbl_message.lower().find("run") > -1 and report:
                    if verbose:
                        print('\nserial_reader:\n    Line received, status report "Run": ' + grbl_message)
                    idle_event.clear()  # Porque GRBL no está IDLE durante el Run.
                    alarm_event.clear()  # Porque home significa que no hay alarma.

                # If Jogging
                elif grbl_message.lower().find("jog") > -1 and report:
                    if verbose:
                        print('\nserial_reader:\n    Line received, status report "Jog": ' + grbl_message)
                    idle_event.clear()  # Porque GRBL no está IDLE durante el Jog.
                    alarm_event.clear()  # Porque home significa que no hay alarma.

                # If feedback MSG
                # https://github.com/gnea/grbl/wiki/Grbl-v1.1-Interface#feedback-messages
                elif grbl_message.upper().find("MSG") > -1:
                    if verbose:
                        print('\nserial_reader:\n    Line received, MSG type: ' + grbl_message)

                    if grbl_message.upper().find("'$X' TO UNLOCK") > -1:
                        idle_event.clear(), alarm_event.set(), unlocked_event.clear(), reset_event.clear()

                    if grbl_message.lower().find("reset to continue") > -1:
                        idle_event.clear(), alarm_event.set(), unlocked_event.clear(), reset_event.set()

                    if grbl_message.upper().find("CAUTION: UNLOCKED") > -1:
                        alarm_event.clear(), unlocked_event.set(), reset_event.clear()

                else:
                    if verbose:
                        print('\nserial_reader:\n    Line received, not classified: ' + grbl_message)

                # If a report was parsed,
                # let the polling thread know that the info is up-to-date
                if report is not None:
                    if verbose:
                        print('\nserial_reader:\n    Marking status tasks done: ' + grbl_message)
                    while request_queue.unfinished_tasks > 0:
                        # Clear all, in case timed-out requests accumulated:
                        request_queue.task_done()

            else:
                # Sleep a bit before checking for serial input again;
                # fastest looping is unnecessary.
                time.sleep(serial_response_delay)

    except Exception as e:
        print("'\nserial_reader:\n    exception in serial_reader!'" + e)
        error_queue.put(e)

    print('\nserial_reader:\n    Loop ended, returning.')
    return True


def queue_grbl_command(line, input_queue, gcode_unlock, verbose=False):
    """
    Use this function to mediate sending of GCODE commands.
    It only wraps a few common commands.
    :param line:
    :param input_queue:
    :param gcode_unlock:
    :param verbose:
    :return:
    """
    # Strip all EOL characters for consistency
    command = line.strip()

    if verbose:
        print('\nqueue_grbl_command:\n   Sending command to serial_writer queue: ' + command)

    # If a setting line, subsequent protocol parsing must be blocked.
    # # The blockade is eventually released by the "serial_writer" thread,
    # # after receiving and parsing the "$" command.
    if command.startswith("$"):
        if verbose:
            print('\nqueue_grbl_command:\n   Sending $ command, locking further gcode. ' + command)
        gcode_unlock.clear()

    # Send the command to the queue read by the "serial_writer" thread
    input_queue.put(command)

    # Hold the main thread until gcode unlocks
    if verbose:
        print('\nqueue_grbl_command:\n   Waiting for gcode_unlock: ' + command)
    gcode_unlock.wait()

    if verbose:
        print('\nqueue_grbl_command:\n   Done sending command: ' + command)

    return command


def serial_writer(serial_interface,
                  input_queue, ok_queue, request_queue, error_queue,
                  idle_event, running_event, alarm_event, unlocked_event, reset_event, gcode_unlock,
                  serial_response_delay=0.1,
                  verbose=True,
                  RX_BUFFER_SIZE=128):
    # Wait for writing request by polling_event.wait()
    # Receive lines from serial_interface
    # Add the output to input_queue
    # Set OK and IDLE events
    # Catch alarm or error states

    exit_code = None

    def status(timeout=None, raise_error=True):
        """
        Report utility function.

        See: https://github.com/gnea/grbl/wiki/Grbl-v1.1-Interface#real-time-status-reports
        """
        # Get the one queue item, thereby blocking other requests, and/or wait until other requests are done.
        request_queue.get()
        serial_interface.write('?'.encode())  # Send "?"

        timed_out = False

        if timeout is None:
            # Wait for task_done in serial_reader to update.
            request_queue.join()
        else:
            endtime = time.time() + timeout
            # Wait for task_done in serial_reader to update.
            while request_queue.unfinished_tasks > 0:
                if endtime - time.time() <= 0.0:
                    print("\ndriver message:\n    ERROR: timed out waiting for status report.")
                    if raise_error:
                        raise GrblError("\ndriver message:\n    ERROR: timed out waiting for status report.")
                    else:
                        timed_out = True
                        break
                time.sleep(serial_response_delay)

        # Flag updated events
        if timed_out:
            idle, alarm = None, None
        else:
            idle = idle_event.is_set()
            alarm = alarm_event.is_set()

        # Put back the item, releasing status requests in other functions.
        request_queue.put("idle")

        return idle, alarm

    def wait_for_idle(timeout=None,
                      raise_error=False):
        """Report utility function"""

        idle, alarm = status(timeout=serial_response_delay,
                             raise_error=False)

        if timeout is None:
            if verbose:
                print("\ndriver message:\n    Waiting for idle (no time out).")
            while not idle:
                idle, alarm = status(timeout=serial_response_delay,
                                     raise_error=False)
                if alarm:
                    print("\ndriver message:\n    Alarm fired while waiting for idle: " + str(timeout))
                    break
        else:
            if verbose:
                print("\ndriver message:\n    Waiting for idle with timeout: " + str(timeout))
            endtime = time.time() + timeout
            while not idle:
                idle, alarm = status(timeout=serial_response_delay,
                                     raise_error=False)
                if endtime - time.time() <= 0.0:
                    print("\ndriver message:\n    ERROR: timed out waiting for status report.")
                    if raise_error:
                        raise GrblError("\ndriver message:\n    ERROR: timed out waiting for status report.")
                    else:
                        break

        return idle, alarm

    if verbose:
        print("\nserial_writer:\n    writer thread started waiting for running_event...")
    running_event.wait()

    if verbose:
        print("\nserial_writer:" +
              "\n    enabled running_event, waiting for commands from input_queue" +
              "\n    Unfinished tasks: " + str(input_queue.unfinished_tasks)
              )

    c_line = []  # Characters in lines sent to GRBL

    try:
        # Loop while running flag is set
        while running_event.is_set():
            # Don't hang if empty
            if input_queue.empty():
                time.sleep(serial_response_delay)
                continue

            # Wait for the next command
            command = input_queue.get()

            # Ignore JOG commands
            if command.startswith("$J"):
                continue

            if verbose:
                print("\nserial_writer:" +
                      "\n    Got command from parser: " + command.strip() +
                      "\n    Unfinished tasks: " + str(input_queue.unfinished_tasks))

            # Strip comments/spaces/new line and capitalize. Note: los comentarios son cosas entre paréntesis.
            command = re.sub(r'\s|\(.*?\)', '', command).upper()
            # Track number of characters in grbl serial read buffer
            c_line.append(len(command) + 1)

            # While there are OK's in the queue, remove oldest "c_line" item
            # This makes the free byte count representative
            if verbose:
                print("\nserial_writer:\n    Clearing ok queue")
            while not ok_queue.empty():
                # Get 'ok' queue items and mark them done
                ok_queue.get()
                ok_queue.task_done()
                # Delete the oldest line from the charcount list
                del c_line[0]

            # Check if the character buffer is getting full...
            if verbose:
                print("\nserial_writer:\n    Checking buffer overflow...")
            while sum(c_line) >= RX_BUFFER_SIZE - 1:
                if verbose:
                    print("\nserial_writer:\n    buffer overflow prevented. Waiting for 'ok'...")
                # Wait for an 'ok' message from GRBL.
                ok_queue.get()
                ok_queue.task_done()
                # When an 'ok' is received, delete the oldest line from the charcount list
                del c_line[0]
                # Thus, the loop ends when the RX_BUFFER_SIZE will not be overflowed by sending another command
                if verbose:
                    print("\nserial_writer:\n    Got 'ok', freeing some buffer and proceeding...")

            # Check if we have a "$" command (home, setting, unlock, jog, ...)
            if verbose:
                print("\nserial_writer:\n    Checking if setting command...")

            # Parse "$" commands
            if command.startswith("$"):
                # If a "$" command we must wait for an all "ok" (task_done),
                # and also wait for GRBL idle state (if not in alarm state, "$X" does not require IDLE).
                # The following ensures that no expected "ok" responses are missing at this point
                #  Accounting for all GCODE sent previously
                #  Note: it would be equivalent to an "input_queue.join" which doesnt count the last ($...) command.
                if verbose:
                    print("\nserial_writer:" +
                          "\n    Setting line received. Waiting for " +
                          str(input_queue.unfinished_tasks) +
                          " unfinished tasks... " + command)

                # If there is more than one task, wait.
                #   There is usually (at least) one task, since this code is running because one was generated :P
                #   So we want only one pending task (the current one) before proceeding.
                while input_queue.unfinished_tasks > 1 and not alarm_event.is_set():
                    if verbose:
                        print("\nserial_writer:\n    " +
                              "input_queue.unfinished_tasks (I) has " +
                              str(input_queue.unfinished_tasks) + " tasks.")

                    # Update status
                    idle, alarm = status()
                    time.sleep(serial_response_delay)

                # If a "locked" or "alarm" event is on, no pending "ok" messages will be received (i guess?),
                # and we must force "get" and "task_done" on the input_queue to clear it.
                if not unlocked_event.is_set() or alarm_event.is_set():
                    while not input_queue.empty():
                        input_queue.get()
                    while input_queue.unfinished_tasks > 0:
                        input_queue.task_done()
                    # Then increment the unfinished tasks by 1 ¿is this stupid?
                    input_queue.put(command)  # It is put...
                    input_queue.get()  # But never sent!

                # Check that only one task is left unmarked
                assert input_queue.unfinished_tasks == 1

                # Wait only if everything is fine (no alarms or locking).
                #  Else warn with some messages.
                if command.startswith("$X") or command.startswith("$H"):
                    print("\nserial_writer:\n    Unlocking command received, sending immediately: " + command)
                else:
                    print("\nserial_writer:\n    GRBL is not alarmed. Waiting for idle before sending: " + command)
                    wait_for_idle()  # Wait for idle or alarm
                    if not unlocked_event.is_set() or alarm_event.is_set():
                        print("\nserial_writer:\n    GRBL is locked/alarmed. Your setting command " +
                              command + " may be ignored by GRBL.")
                    # https://github.com/gnea/grbl/wiki/Grbl-v1.1-Interface#alarm-message

            # Alarm state check for non setting commands
            elif not unlocked_event.is_set() or alarm_event.is_set():
                print("\nserial_writer:\n    GRBL is locked/alarmed. Your setting command " +
                      command + " may be ignored by GRBL or produce error messages.")

            # Send the command to GRBL's serial interface
            if verbose:
                print("\nserial_writer:\n    Sending command to serial interface: " + command)
            serial_interface.write(str.encode(command + '\n'))

            # If it was a "$..." line, wait for the "ok" response.
            if command.startswith("$"):
                if verbose:
                    print("\nserial_writer:" +
                          "\n    Waiting for input queue join with unfinished_tasks: " +
                          str(input_queue.unfinished_tasks))

                # Wait for all "ok"s to be collected (should be just one for setting lines).
                input_queue.join()

                if verbose:
                    print("\nserial_writer:\n    Lifting gcode blockade...")

                # Finally release protocol progress
                gcode_unlock.set()

            if verbose:
                print("\nserial_writer:\n    Done sending command: " + command +
                      ". Remaining buffer: " + str(RX_BUFFER_SIZE - 1 - sum(c_line)))

            # Wait for the next command
            continue

    except GrblError as e:
        print("\nserial_writer:\n    GRBL error exception called during protocol streaming:\n    ", e)
        exit_code = 1

    except AssertionError as e:
        print(e)
        print("\nserial_writer:\n    assertion error in serial_writer!")
        error_queue.put(e)
        exit_code = 2

    except Exception as e:
        print("\nserial_writer:\n    Uncaught exception in serial_writer!: " + str(e))
        error_queue.put(e)
        exit_code = 3

    else:
        # Run if the try clause completes
        exit_code = 0

    finally:
        if verbose:
            print("\nserial_writer:\n    writer thread ending with exit code: " + str(exit_code))

    return exit_code
