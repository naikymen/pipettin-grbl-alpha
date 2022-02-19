def gcodeSetFeedrate(feedrate):
    """Set feedrate for G1 moves"""
    return "G0 F" + str(feedrate)


def gcodeSpindleEnable():
    """M3 as per http://linuxcnc.org/docs/html/gcode/m-code.html#mcode:m3-m4-m5"""
    return "M3 S0"


def gcodeSpindleDisable():
    """M5 as per http://linuxcnc.org/docs/html/gcode/m-code.html#mcode:m3-m4-m5"""
    return "M5"


def gcodeEjectTip():
    """Tip ejection by servo, controlled thourh pigpio"""
    return ["Peject;"]
    #"M5 as per http://linuxcnc.org/docs/html/gcode/m-code.html#mcode:m3-m4-m5"
    #return ["M3 S20", "Wait;1", "M3 S80"]


def gcodeProbeZ(z_probe=12, x_probe=0, y_probe=0, z_scan=-2.5, probe_height=52):
    # "G38.2" probe until probe is ON, error if probe doesnt activate during probing
    # "G38.3" probe until probe is ON, without error
    return ["G90 G0 X{} Y{}".format(x_probe, y_probe),
            "G90 G0 Z{}".format(str(z_probe+1)),
            "G91 G0 Z-1",
            "G38.2 Z{} F200".format(str(z_scan)),
            "G92 Z{}".format(probe_height),
            "G90 G0 Z{}".format(str(probe_height + 10))
            ]


def gcodePipetteProbe(z_scan=-2.5, mode="G38.2", feedrate=200):
    # "G38.2" probe until probe is ON, error if probe doesnt activate during probing 
    # "G38.3" probe until probe is ON, without error.
    # TODO: conseguir informacion del probe position con "$#".
    #  Ver: https://github.com/gnea/grbl/wiki/Grbl-v1.1-Commands#---view-gcode-parameters
    # assert z_scan <= 0
    return "{} Z{} F{}".format(mode, str(z_scan), str(feedrate))


def gcodeMove(x: float = None,
              y: float = None,
              z: float = None,
              s: float = None,
              _mode="G90 G0",  # G90 for absolute, G91 for relative
              _scale_servo=1):
    """gcode to move robot to xyz and servo to s, by pasting values of xyzs if specified """

    if x is None and y is None and z is None and s is None:
        print("No values specified, returning empty string.")
        return ""

    command = [_mode]  # Default is G90 G0,

    if x is not None:
        command.append("X" + str(x))

    if y is not None:
        command.append("Y" + str(y))

    if z is not None:
        command.append("Z" + str(z))

    if s is not None:
        command.append("S" + str(s/_scale_servo))

    return " ".join(command)


def gcodeHomeXYZ(which_axis="all"):
    """Returns $H for 'all' or either single axis homing commands for which_axis equal to x, y or z."""
    
    # Default GRBL homing command
    home_command = "$H"

    # Append single axis specifier if required
    if which_axis != "all" and which_axis.upper().find("XYZ") == -1:
        if which_axis.upper().find("X") >= 0:
            home_command += "X"
        if which_axis.upper().find("Y") >= 0:
            home_command += "Y"
        if which_axis.upper().find("Z") >= 0:
            home_command += "Z"

    return home_command


def gcodeG92(x: float = None,
             y: float = None,
             z: float = None):
    """Returns G92 setup command"""
    command = ["G92"]  # Default is G90 G0,

    if x is None and y is None and z is None:
        print("gcodeMove warning: no values specified.")
        return "; gcodeMove warning: no values specified"

    if x is not None:
        command.append("X" + str(x))

    if y is not None:
        command.append("Y" + str(y))

    if z is not None:
        command.append("Z" + str(z))

    return " ".join(command)
