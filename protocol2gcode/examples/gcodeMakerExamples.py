import driverGcodeSender as gcode

# Example construction of protocols, as lists of basic gcode constructors.
# A custom constructor can be built from these functions.
# As long as the output is a list of strings, each a valid GCODE command, everything will be fine.
import gcodePrimitives

protocol_setupCNC = [
    gcodePrimitives.gcodeHomeXYZ(),
    gcodePrimitives.gcodeG92(x=-115, y=-110, z=30.5),
    gcodePrimitives.gcodeSpindleEnable()
]

protocol_homeCNC = [
    gcodePrimitives.gcodeHomeXYZ()
]

protocol_moveCNC = [
    gcodePrimitives.gcodeMove(x=10, y=0, z=0, s=0)
]

# GCODE can be written directly into a list and passed to gcodeProtocolSend().
protocol_Dance = [
    "M3 S1",
    "M3 S100",
    "M3 S50",
    "G90 G0 X10 Y10 Z10 S1",
    "G90 G0 X0 Y10 Z0 S50",
    "G90 G0 X0 Y0 Z10 S100",
    "G90 G0 X10 Y0 Z20 S1",
    "G90 G0 X10 Y10 Z10 S1"
]

# gcodeProtocolSend(protocol_homeCNC, serialdevicepath='/dev/ttyACM1')
gcode.gcodeProtocolSend(protocol_setupCNC,
                        serialdevicepath='/dev/ttyACM1')
# gcodeProtocolSend(protocol_moveCNC, serialdevicepath='/dev/ttyACM1')
gcode.gcodeProtocolSend(protocol_Dance,
                        serialdevicepath='/dev/ttyACM1')
gcode.gcodeProtocolSend([gcodePrimitives.gcodeSpindleDisable()],
                        serialdevicepath='/dev/ttyACM1')
