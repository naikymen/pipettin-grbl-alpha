#!/usr/bin/python3
from collections import namedtuple
from commander_utils import run_commander
import time
import systemd.daemon
import socketio

# Commander systemd service
# Based on this guide: https://github.com/torfsen/python-systemd-tutorial
# Thanks!

"""
Systemd unit definition, located at "/home/pi/.config/systemd/user/commander.service".

Tracked by the git repo at "systemd.units/commander.service". See the README file at its directory.

The unit can be enabled with these commands:

$ systemctl --user daemon-reload  # reload user service files after editing
$ systemctl --user enable commander.service  # enable service on boot

Importantly, run "sudo loginctl enable-linger $USER" at least once as the pi user.

Also run "apt-get install python-systemd python3-systemd" to install the systemd python module.

To test this, a useful command is:

systemctl --user restart commander.service; journalctl --user-unit commander -f  # restart serviceand follow the logs
"""

busy = False


def command_message_handler(new_args):
    """
    Handler for 'p2g_command' socket events.
    :param new_args: a named tuple with updated arguments.
    :return: process exit code.
    """
    global busy

    if busy:
        print("Received GUI command while the commander is busy, ignoring call with content: " + str(new_args))
        e_code = 1
    else:
        # If we weren not busy, we must be now! :)
        busy = True

        print("Received GUI command while the commander is idle, parsing call with content: " + str(new_args))
        # Pre-process arguments
        args = parse_args(new_args)
        try:
            # Parse arguments and execute actions on the robot
            e_code = run_commander(sio, args)
        except Exception as e:
            print("Exception at run_commander() call: " + str(e))
            e_code = 1

        # Mark not busy
        busy = False

    # Exit code return
    return e_code


def parse_args(new_args):
    """
    Pre-process arguments into a named tuple, overwriting default values.
    :param new_args: dictionary with new arguments.
    :return: a named tuple with updated arguments.
    """

    # Fix invalid name for namedtuple conversion
    if "run-protocol" in new_args.keys():
        new_args["run_protocol"] = new_args.pop("run-protocol")

    # Default arguments
    dflt = {"port": None,
            "baudrate": None,
            "run_protocol": None,
            "calibration": None,
            "mongo_url": 'mongodb://localhost:27017/',
            "workspace": None,
            "pipette_model": "p200",
            "item": None,
            "content": None,
            "move": None,
            "distance": None,
            "command": None,
            "home": None,
            "s_retract": 16.8,
            "interactive": False,
            "dry": False,
            "verbose": True}

    # Update default with new values
    dflt.update(new_args)

    # Convert to named tuple (analogue for "parser.parse_args()"
    args = namedtuple("Arguments", dflt.keys())(*dflt.values())

    return args


if __name__ == '__main__':

    """
    Arguments:
        port
        baudrate
        run-protocol
        calibration
        workspace
        item
        content
        move
        distance
        command
        home
        s_retract
        interactive
        dry
        verbose
    """

    print('Starting up ...')

    # Instantiate socket object
    sio = socketio.Client()
    sio.on('p2g_command', command_message_handler)
    while True:
        try:
            if not sio.connected:
                socket_port = 3333
                # Connect to socket
                sio.connect('http://localhost:' + str(socket_port))
        except socketio.exceptions.ConnectionError as err:
            print("Socket.io ConnectionError: " + str(err) + ". Retrying in 5 seconds.")
            systemd.daemon.notify('RELOADING=1')  # https://www.freedesktop.org/software/systemd/man/sd_notify.html#
        except Exception as err:
            print("Commander.py unexcpecte derror: " + str(err) + ". Stopping")
            sio.disconnect()
            systemd.daemon.notify("STOPPING=1")
            break
        else:
            if sio.connected:
                print("Websocket connected!")
                systemd.daemon.notify('READY=1')  # https://www.freedesktop.org/software/systemd/man/sd_notify.html#
        time.sleep(5)
    # Register websocket event listener function for "start human intervention"
    # sio.on('human_intervention_continue', continue_message_handler)
    # Register websocket event listener function for "cancelled human intervention"
    # sio.on('human_intervention_cancelled', abort_message_handler)  # initialize event listener

