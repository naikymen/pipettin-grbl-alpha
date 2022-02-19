import driverGcodeSender as Gcode
import gcodePrimitives


def actionHOME():
    home_sweet_home = gcodePrimitives.gcodeHomeXYZ()
    print(home_sweet_home)
    return home_sweet_home


def actionPICK_TIP(_action):
    # move to clearance level on Z
    # move to next tip location on XY
    # move to Z just on top
    # seal the tip by pressing a little bit very slowly two times
    # move to clearance level on Z

    return _action["args"]


def actionLOAD_LIQUID(_action):
    # move to clearance level on Z
    # move to next tube location on XY
    # move to Z at loading height
    # load liquid
    # move to clearance level on Z

    return _action["args"]


def actionDROP_LIQUID(_action):
    # move to clearance level on Z
    # move to next tube location on XY
    # move to Z at dispensing height
    # dispense liquid
    # move to clearance level on Z

    return _action["args"]


def actionDISCARD_TIP(_action):
    # move to clearance level on Z
    # move over discarding bucket
    # eject tip
    # move to clearance level on Z

    return _action["args"]


switch_case = {
    "HOME": actionHOME,
    "PICK_TIP": actionPICK_TIP,
    "LOAD_LIQUID": actionLOAD_LIQUID,
    "DROP_LIQUID": actionDROP_LIQUID,
    "DISCARD_TIP": actionDISCARD_TIP
}

switch_case["HOME"]()