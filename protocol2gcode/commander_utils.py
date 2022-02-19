# import gcodePrimitives
import pprint
import pymongo
from gcodeBuilder import GcodeBuilder
# from commander_utils import MongoObjects
from gcodeCommander import Commander
import gcodePrimitives
# from pipetteDriver import Pipette
import re
# import sys
import time


class MongoObjects(object):
    """A class holding machine current status or configuration, a class for machine state tracking."""
    """Also holds all GCODE commands after parsing protocols."""

    def __init__(self, mongo_url='mongodb://localhost:27017/', parser_object=None, verbose=True, pipette=None):

        self.parser_object = parser_object
        self.verbose = verbose
        self.mongo_url = mongo_url

        self.pipette = pipette

        # DATABASE SETUP ############

        # connect and select database name
        if self.verbose:
            print("commanderTest.py message: Connecting to mongodb")
        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client['pipettin']

        # collection names
        self.collectionProtocols = self.db['protocols']
        self.collectionWorkspaces = self.db['workspaces']
        self.collectionPlatforms = self.db['platforms']

        # ensure indexes
        self.collectionProtocols.create_index([('name', pymongo.ASCENDING)], unique=True)
        self.collectionWorkspaces.create_index([('name', pymongo.ASCENDING)], unique=True)
        self.collectionPlatforms.create_index([('name', pymongo.ASCENDING)], unique=True)

    def makeGoToPlatformCommand(self, workspace_name, platform_name, content_name):
        """
        Annoying function to calculate platform position.
        Should be replaced with something from the TaskClass stuff.
        """

        # Get workspace object
        workspace = self.collectionWorkspaces.find_one({"name": workspace_name})
        if not workspace:
            if self.parser_object is None:
                raise Exception("makeGoToPlatformCommand: protocol's workspace not found.")
            else:
                self.parser_object.error("protocol's workspace not found.")

        # Get platform names in workspace
        platform_names = list(map(lambda p: p['platform'], workspace['items']))

        # Get platforms in workspace
        platforms_in_workspace = list(self.collectionPlatforms.find({"name": {"$in": platform_names}}))

        platform_item = self.getWorkspaceItemByName(workspace=workspace, platform_name=platform_name)

        platform = self.getPlatformByName(platformsInWorkspace=platforms_in_workspace, platform_item=platform_item)

        content = self.getContentByName(content_name=content_name, platform_item=platform_item)

        # Calculate XY of tube center
        _x = platform_item["position"]["x"]
        _x += platform['firstWellCenterX']
        _x += content["position"]["col"] * platform['wellSeparationX']

        _y = platform_item["position"]["y"]
        _y += platform['firstWellCenterY']
        _y += content["position"]["row"] * platform['wellSeparationY']

        if self.verbose: 
            print("makeGoToPlatformCommand message:\n    Moving to position: X" + str(_x) + " Y" + str(_y))
            print("makeGoToPlatformCommand message:\n    To platform:", platform)

        command = gcodePrimitives.gcodeMove(x=_x, y=_y)

        # Calculate Z for pipetting #########################################################
        # TODO: check and tune Z positioning according to tip seal pressure or seal distance,
        #  this might need calibration. Ver issue #7 y #25
        # https://github.com/naikymen/pipettin-grbl/issues/7
        # https://github.com/naikymen/pipettin-grbl/issues/25

        # First reference is the "bottom" of the tube
        default_bottom_position = platform["defaultBottomPosition"]
        _z = default_bottom_position
        
        # Increase height because a tip is placed
        tip_length = self.pipette["tipLength"]  # p200 default is 50
        _z += tip_length

        # Decrease height because the pipette sinks into the tip to make the "seal"
        tip_seal_distance = self.pipette["tipSealDistance"]  # p200 default is 6
        _z += -tip_seal_distance  # TO-DO: how should this be callibrated?

        message = "Default pipetting position for the platform is: " + str(default_bottom_position)  # + "\n"
        message += ". The tip length is: " + str(tip_length)
        message += ". The tip sealing distance is: " + str(tip_seal_distance)
        message += ". Such that the final pipetting Z position would be: " + str(_z)

        message += "\n\n"
        message += "You might want to move the Z axis manually to that position, with a tip placed, "
        message += "and check if the tip is about 1 mm above the bottom of the tube. "
        message += "That is a good height for small volumes (10-200 ul)."

        return command, message

    def getProtocolObjects(self, protocol_name):
        """
        Annoying function to make protocol gcode.
        Should be moved into the task class thing.
        """

        # ARGUMENT CHECKS ############

        # arg is required
        if type(protocol_name) is not str:
            if self.parser_object is None:
                raise Exception("getProtocolObjects: run-protocol is required.")
            else:
                self.parser_object.error("run-protocol is required.")

        # get protocol data by name
        protocol = self.collectionProtocols.find_one({"name": protocol_name})
        if not protocol:
            if self.parser_object is None:
                raise Exception("getProtocolObjects: protocol not found.")
            else:
                self.parser_object.error("protocol not found.")

        # get protocol's workspace data
        workspace = self.collectionWorkspaces.find_one({"name": protocol['workspace']})
        if not workspace:
            if self.parser_object is None:
                raise Exception("getProtocolObjects: protocol's workspace not found.")
            else:
                self.parser_object.error("protocol's workspace not found.")

        # DATABASE QUERIES ############

        # extract platform names in workspace
        platform_names = list(map(lambda p: p['platform'], workspace['items']))
        # get platforms in workspace
        platforms_in_workspace = list(self.collectionPlatforms.find({"name": {"$in": platform_names}}))

        return protocol, workspace, platforms_in_workspace

    def getWorkspaceItemByName(self, workspace, platform_name):
        """Iterate over items in the workspace looking for one who's name matches 'platform_name' """
        for item in workspace["items"]:
            if item["name"] == platform_name:
                return item
            else:
                continue
        return None

    def getPlatformByName(self, platformsInWorkspace, platform_item):
        """Iterate over platforms in workspace looking for one who's name matches the platform in 'platform_item' """
        for platform in platformsInWorkspace:
            if platform["name"] == platform_item["platform"]:
                return platform
            else:
                continue
        return None

    def getContentByName(self, content_name, platform_item):
        for content in platform_item["content"]:
            if content['name'] == content_name:
                return content
            else:
                continue
        return None


def run_commander(sio, args):
    """
    This function decides how and what to send to the robot, based on the set of arguments provided by the GUI.
    :param sio: socketio.Client() object, connected and ready to use.
    :param args: namedtuple with arguments from the GUI call (ex-args from CLI argument parser)
    :return: nothing :)
    """

    verbose = args.verbose

    # Instantiate
    commander = Commander(
        serial_device_path=args.port, baudrate=args.baudrate,
        pipette_model=args.pipette_model,
        sio_object=sio,  # Defined below as socketio.Client()
        pipette_homing_retraction=float(args.s_retract),
        dry=args.dry, interactive=args.interactive,
        verbose=args.verbose)

    # Decide what to do, and send commands accordingly:
    if args.run_protocol is None:

        # Home command
        if args.home is not None:

            if verbose:
                print("commander.py message: sending home command: " + args.home)

            pattern = re.compile(".?[xyz]")
            if pattern.match(args.home) is not None:
                # Build gcode
                home_sweet_home = gcodePrimitives.gcodeHomeXYZ(which_axis=args.home)
                # Send command to GRBL
                commander.send_to_serial(command=home_sweet_home)
                commander.update_sio_wpos(timeout=30)

            if args.home.upper().find("P") > -1 or args.home.upper() == "ALL":
                if verbose:
                    print("---- Sending pipette axis home...")
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
                if verbose:
                    print("commanderTest.py message: sending Pipette move: " + args.distance)
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
                    "commanderTest.py message: sending 'goto' command as fast_grbl_command: " + args.calibration)
                print("    Using workspace: " + args.workspace)
                print("    Using item: " + args.item)
                print("    Over content: " + args.content)

            # Setup database
            database_tools = MongoObjects(mongo_url=args.mongo_url,
                                          parser_object=None,  # argparse no longer used
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
            if verbose:
                print("commanderTest.py message: Nothing done: no protocol, move or home options provided.")

    # Run a protocol
    elif args.run_protocol is not None:
        if verbose:
            print("commanderTest.py message: Provided protocol name: '" + args.run_protocol + "'\n")

        if verbose:
            print("\ncommanderTest.py message: Loading protocol objects from MONGODB.\n")
        # Setup database
        database_tools = MongoObjects(mongo_url=args.mongo_url,
                                      parser_object=None,  # argparse no longer used
                                      verbose=args.verbose,
                                      pipette=commander.pipette.pipette)

        # Load protocol objects from mongodb:
        protocol, workspace, platforms_in_workspace = database_tools.getProtocolObjects(protocol_name=args.run_protocol)

        if verbose: print("\ncommanderTest.py message: Instantiating protocol task class.\n")

        # Initiate the task class, which will hold all relevant information for the current task
        builder = GcodeBuilder(protocol, workspace, platforms_in_workspace,
                               setup=False, s_retract=-float(args.s_retract))

        # TODO WORKAROUND: Replace the pipette with the one used by the commander ¿already done?
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
            "The call to commander.py couldn't be matched to an action. Causes: bad arguments or source code :P")

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

    return 0
