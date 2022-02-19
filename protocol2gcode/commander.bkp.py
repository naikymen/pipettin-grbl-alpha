import argparse
import pprint
import pymongo
from gcodeBuilder import GcodeBuilder
from commander_utils import MongoObjects
from gcodeCommander import Commander
import gcodePrimitives
from pipetteDriver import Pipette
import re
import sys
import socketio
import time

# python3 -u ../protocol2gcode/commanderTest.py --port /dev/ttyACM0 --baudrate 115200 --run-protocol test1 2020-08-10T02:46:19.190Z
# python3 commanderTest.py --port /dev/ttyACM0 --baudrate 115200 --run-protocol "Simple Protocol"

print("Commander called, initiating...")

parser = argparse.ArgumentParser()

parser.add_argument('--port', help='Serial Port name')
parser.add_argument('--baudrate', help='Baudrate')

parser.add_argument('--run-protocol', help='Protocol name', default=None)
parser.add_argument('--calibration', help='Calibration type')
parser.add_argument('--workspace', help='Worksapce name')
parser.add_argument('--item', help='Item name')
parser.add_argument('--content', help='Content name')

parser.add_argument('--move', help='Move')
parser.add_argument('--distance', help='mm to move (or volume, for the pipette axis)', default=None)
parser.add_argument('--command', help='send GRBL command', default=None)
parser.add_argument('--home', help='home', default=None)

parser.add_argument('--s_retract', help='Pipette retraction in millimeters, applied after homing.', default=16.8)

parser.add_argument('--interactive',
                    help='Interactive CLI input',
                    default=False,
                    action="store_true")  # 1 is True, enabled.
parser.add_argument('--dry',
                    help='Skip sending gcode',
                    default=False,
                    action="store_true")  # 1 is True, enabled.
parser.add_argument('--verbose',
                    help='Print many many messages',
                    default=True,
                    action="store_true")

args = parser.parse_args()
verbose = args.verbose

if verbose:
    print("args.port: " + str(args.port))
    print("args.baudrate: " + str(args.baudrate))
    print("args.workspace: " + str(args.workspace))
    print("args.item: " + str(args.item))
    print("args.content: " + str(args.content))
    print("args.calibration: " + str(args.calibration))
    print("args.run-protocol: " + str(args.run_protocol))
    print("args.command: " + str(args.command))
    print("args.move: " + str(args.move))
    print("args.distance: " + str(args.distance))
    print("args.home: " + str(args.home))
    print("args.interactive: " + str(args.interactive))
    print("args.dry: " + str(args.dry))

######### COMMANDER SETUP (replaces old gcode sender) #########

# Instantiate
commander = Commander(
    serial_device_path=args.port, baudrate=args.baudrate,
    pipette_model="p200",
    pipette_homing_retraction=float(args.s_retract),
    dry=args.dry, interactive=args.interactive,
    verbose=args.verbose)

"""
######### Some toy examples ------------------------- #########

# Import module
from gcodeCommander import Commander
from commander_utils import MongoObjects

# Instantiate
commander = Commander()

# Setup threads
commander.start_threads()

# Check if it responds to status requests
commander.status(2)
# Setup
commander.check_grbl_status()
commander.steppers_on()
commander.steppers_off()
# Play
commander.send_gcode("$H")
commander.fast_jog("G91 G0 X1")
commander.sio_emit("alert", {'text': "ALARM message from GRBL:", 'type': 'alarm'})
commander.tip_eject()
commander.pipette_displace(";5", 0)
commander.pipette_displace_volume(20)
commander.pipette_home()
commander.wait(";5")
# Cleanup
commander.cleanup()

# Database objects
dbtools = MongoObjects(mongo_url='mongodb://localhost:27017/'

# https://stackoverflow.com/a/34598654
from pprint import pprint
cursor = dbtools.collectionProtocols.find()
for document in cursor:
    pprint(document)
protocol = dbtools.collectionProtocols.find_one({"name": 'digestion_hele3 2021-05-25T17:31:42.737Z'})
"""

######### Interpret the call #########

# try:

if args.run_protocol is None:

    # Home command
    if args.home is not None:

        if verbose: print("commander.py message: sending home command: " + args.home)

        pattern = re.compile(".?[xyz]")
        if pattern.match(args.home) is not None:
            # Build gcode
            home_sweet_home = gcodePrimitives.gcodeHomeXYZ(which_axis=args.home)
            # Send command to GRBL
            commander.send_to_serial(command=home_sweet_home)
            commander.update_sio_wpos(timeout=30)

        if args.home.upper().find("P") > -1 or args.home.upper() == "ALL":
            if verbose: print("---- Sending pipette axis home...")
            # Home
            commander.pipette_home()
            # Then move up a bit, equivalent to 20 uL of the p200: 20 / (pi*((4/2)**2)) ~ 1.59
            commander.pipette_displace(";1.59", 0)

    # Move command (as Jog)
    elif args.move is not None:
        move_direction = str(args.move).lower()
        if move_direction in ["x", "y", "z"]:
            # Build gcode
            move_params = {"x": None, "y": None, "z": None}
            move_params[move_direction] = args.distance
            move_command = gcodePrimitives.gcodeMove(_mode="G91 G0",
                                                     x=move_params["x"],
                                                     y=move_params["y"],
                                                     z=move_params["z"])
            if verbose:
                print("commanderTest.py message: sending GRBL jog command: " + move_command)
            # Send command to GRBL
            # commander.serial(fast_grbl_command=move_command)
            commander.send_to_serial(command=move_command)
            time.sleep(0.2)  # Wait for move to start
            commander.update_sio_wpos(timeout=30)

        if move_direction == "p":
            if verbose: print("commanderTest.py message: sending Pipette move: " + args.distance)
            # pipette = Pipette(pipette="p200", home_pipette_at_init=False, dry=args.dry)
            # pipette.displace(displacement=args.distance)
            # pipette.close()
            commander.pipette.displace(displacement=args.distance)
            # commander.pipette_displace_volume(float(args.distance))

    # Fast command (non-move)
    elif args.command is not None:
        if verbose:
            print("commanderTest.py message: sending other GRBL fast command (non-move): " + args.command)
        # Send command directly to the serial port
        commander.send_to_serial(command=args.command + "\n")

    # Go-to platform item command
    elif args.calibration == "goto":
        if verbose:
            print(
                "commanderTest.py message: sending 'goto' calibration command as fast_grbl_command: " + args.calibration)
            print("    Using workspace: " + args.workspace)
            print("    Using item: " + args.item)
            print("    Over content: " + args.content)

        # Setup database
        database_tools = MongoObjects(mongo_url='mongodb://localhost:27017/',
                                      parser_object=parser,
                                      verbose=args.verbose,
                                      pipette=commander.pipette.pipette)

        # Generate move command
        command, message = database_tools.makeGoToPlatformCommand(workspace_name=args.workspace,
                                                                  platform_name=args.item,
                                                                  content_name=args.content)

        # Verbose alert stuff
        commander.sio_emit('alert', {"text": message})

        # Send command directly to the serial port
        if verbose:
            print("commanderTest.py message: sending command to serial: " + command)
        commander.send_to_serial(command=command + "\n")

        # Request status update
        if verbose:
            print("commanderTest.py message: requesting wpos status update for socketio emit: " + command)
        time.sleep(0.2)  # Wait for move to start
        commander.update_sio_wpos(timeout=10)

    else:
        if verbose: print("commanderTest.py message: Nothing done: no protocol, move or home options provided.")

# Run a protocol
elif args.run_protocol is not None:
    if verbose:
        print("commanderTest.py message: Provided protocol name: '" + args.run_protocol + "'\n")

    if verbose: print("\ncommanderTest.py message: Loading protocol objects from MONGODB.\n")
    # Setup database
    database_tools = MongoObjects(mongo_url='mongodb://localhost:27017/',
                                  parser_object=parser,
                                  verbose=args.verbose,
                                  pipette=commander.pipette.pipette)

    # Load protocol objects from mongodb:
    protocol, workspace, platformsInWorkspace = database_tools.getProtocolObjects(protocol_name=args.run_protocol)

    if verbose: print("\ncommanderTest.py message: Instantiating protocol task class.\n")
    # Initiate the task class, which will hold all relevant information for the current task
    builder = GcodeBuilder(protocol, workspace, platformsInWorkspace, setup=False, s_retract=-float(args.s_retract))
    # TODO WORKAROUND: Replace the pipette with the one used by the commander
    builder.pipette = commander.pipette.pipette
    # Generate GCODE for the task, it is saved in the task class object
    builder.parseProtocol()

    # Get the command list, and pass it on to the commander.
    commander.protocol = builder.commands

    # Print it
    if verbose:
        pprint.pprint(commander.protocol)

    # Send the GCODE. TODO: serial path and baudrate can be specified here
    if verbose:
        print("\ncommanderTest.py message: Sending protocol\n")
    commander.run_protocol()

else:
    raise Exception(
        "The call to commander.py was not matched to any of the available conditions. Cuases: bad arguments or bad source code :P")

# except Exception as err:
#     print("Exception caught in commander main try clause:", err)
#     # Exit cleanly
#     commander.cleanup()
#     sys.exit(1)

# else:
#     print("commanderTest.py message: done!")
#     # Exit cleanly
#     commander.cleanup()
#     sys.exit(0)

print("commanderTest.py message: done!")
commander.cleanup()
sys.exit(0)
