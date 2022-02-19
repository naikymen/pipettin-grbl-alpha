# Electronics

El diagrama de conexiones está en el archivo `diagrama_conexiones`.

El formato `cddx` puede editarse en: https://www.circuit-diagram.org/editor/

## RPi as master controller

### Connections

To GRBL, using a standard USB cable.

To the Pololu and the limit switch, using the GPIO header.

To the arduino reset pin, from the GPIO header and through a transistor.

### Pipette pololu capacitor

Prevents voltage spikes :) it is connected across the main 24 Volt line.

## CNC Shield 3.0 and Modifications

A CNC Shield v3.0 clone.

### Pololu Vref adjustment

Set to 1.1 V, limiting total machine current to less than 2 A. Could be less I guess, haven't tested.

https://wiki.frubox.org/proyectos/diy/cnc#ajuste-vref-pololu

More voltage means more reliable stepping, and means less current, which means less heat.

### Cooling fan

Stepper drivers can overheat at higher Vref without a cooling fan.

In all cases, the longer the run the more important cooling became.

Use a fan always, just in case.

### Clone the Y axis to A

We have a double Y axis, pins are setup accordingly.

Note: no square gantry, its incompatible with our 3.0 shield clone.

### Invert pins 11 and 12

Tu use with variable spindle GRBL 1.1h, we inverted pins 11 and 12.

This allows us to use the variable spindle PWM function to drive a servo (see `grbl/LEEME.md`).

See also: https://wiki.frubox.org/proyectos/diy/cnc#z-axis-limit-switch

### Servo-motor for tip ejection

Using the default pin for variable spindle in GRBL 1.1h (note that a rewire is important if using an old CNC Shield v3.0 clone; this is described above).

5V step-down power supply.

### Reset pin capacitor

Putting a capacitor between reset and GND prevents arduino reset on pyserial open/reconection (it also prevents uploading new firmware, do it after flashing GRBL :).

https://forum.arduino.cc/index.php?topic=21479.msg159720#msg159720

### Arduino reset from GPIO

Sometimes the Arduino needs to be reset by the RPi.

The voltages are different (3.3V GPIO vs 5V Arduino).

So, a transistor is useful for resetting/unlocking GRBL.

We used a PNP transistor in stead of an NPN, but the concept is the same as in: https://electronics.stackexchange.com/a/180709

### Stepper wiring and directions

Important for correct workspace coordinate system.

See: https://wiki.frubox.org/proyectos/diy/cnc#stepper-wiring-y-sistema-de-coordenadas

### End-stops and modifications

Important for homing.

## CNC shield hat

A small hat to tidy up some of the modifications of the CNC Shield described previously.

KiCAD designs for the hat are in the `cnc_shield_hat` directory.

Also, KiCAD designs for the a CNC Shield are in the `sb-cnc-shield` (cloned repository from GitHub, not used here).

Settings for pcb2gcode[GUI] and a sample command are in the `pcb2gcode` directory.

### KiCAD 101

A simple video showing the basic workflow: https://www.youtube.com/watch?v=-tN14xlWWmA

### Installing and using pcb2gcode

This translates gerber files to millable gcode.

pcb2gcode might be moderately hard to install. I had to modeify a header file on `gerbv` 's source code for it to compile on modern GCC.

Then, to compile `pcb2gcode` with the headers in the `gerbv` I built in the previous step, it is important to set an environmen variable before running `./configure`:

    export PKG_CONFIG_PATH=~/Software/pcb2gcode/gerbv-2.7.0/src

The GUI was cloned, built, and installed without issues on my system.

There are some GRBL-specific configurations for `pcb2gcode`. Once taken into account, only minor modifications of the gcode are necessary.

Read for details: https://wiki.frubox.org/proyectos/diy/cnc/kicad_pcb

### Preview of the GCODE

This can be done on bCNC directly or on http://chilipeppr.com/grbl (or http://chilipeppr.com/jpadie).

### Editing and sending gcode with bCNC

The only important edits are:

  * Optional: add a homing cycle and your G92 command.
  * Remove unnecessary header commands.

https://wiki.frubox.org/proyectos/diy/cnc#bcnc

# To-do 

Completar este readme.
