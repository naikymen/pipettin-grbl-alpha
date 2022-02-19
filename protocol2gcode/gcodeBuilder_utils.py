# These functions read and iterate over "protocols"
# And call other constructor functions to translate "actions" into GCODE

# import driverGcodeSender as Gcode
import gcodePrimitives
import sys


def actionParser(i, action, task):
    """This function interprets actions in the JSON file and produces a GCODE version of the protocol"""
    # Python switch case implementations https://data-flair.training/blogs/python-switch-case/
    # All action interpreting functions will take two arguments
    # action: the action object
    # i: the action index for the current action
    # task: the object of class "TaskEnvironment"

    # Register new action start as comment in the GCODE
    task.commands.extend(["; Building action " + str(i) + ", with command: " + str(action["cmd"])])

    # List of available macros for the requested actions
    # TODO: implement repeat dispensing
    # TODO: implement reverse pipetting
    # TODO: implement available/maximum volume checks
    switch_case = {
        "HOME": task.actionHOME,
        "PICK_TIP": task.macroPickNextTip,
        "LOAD_LIQUID": task.macroGoToAndPipette,
        "DROP_LIQUID": task.macroGoToAndPour,
        "DISCARD_TIP": task.actionDISCARD_TIP,
        "PIPETTE": task.macroPipette,
        "COMMENT": task.actionComment,
        "HUMAN": task.actionHuman
    }
    # Produce the GCODE for the action
    try:
        print("\nProcessing command", action["cmd"], "with index", str(i))
        action_function = switch_case[action["cmd"]]
        action_commands = action_function(action, i)
    except Exception as err:
        print("\nERROR: protocolInterpreter at action with index " + str(i) + " and command: " + action["cmd"])
        print("Error message:", err)
        sys.exit("Protocol parser error!")

    print(action_commands)

    return action_commands


def runProtocolParser(task):
    """This function takes a task object and parses its actions into gcode"""

    # TODO: que los actions guarden su index en el dict, así no tengo que generarlos acá
    protocol_parsed = [actionParser(i, action, task) for i, action in enumerate(task.protocol["actions"])]

    # Disable spindle at the end -- DEPRECATED
    # task.commands.append(gcodePrimitives.gcodeSpindleDisable())

    # Get GCODE
    protocol_gcode = task.getGcode()

    # return protocol_parsed
    return protocol_gcode
