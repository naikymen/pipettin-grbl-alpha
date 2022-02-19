# Pipettin' GRBL

Pipetting robotware for laboratory protocol automation.

![mender1_cdnm_mazinger](doc/media/pics/21_04-en_el_labo/IMG_7441.JPG)

## Installation on RPi 4

Restore our SD card image:

```
gunzip --stdout pipettin_pi.img.gz | sudo dd bs=4M of=/dev/YOUR_SD_CARD_DEVICE
```

See: https://www.raspberrypi.org/documentation/linux/filesystem/backup.md

Background services are managed by `systemd` user units `commander.service` and `nodegui.service` (both defined at `/home/pi/.config/systemd/user`, enabled by default).

## Requirements

Requirements _at a glance_.

### Hardware

* Raspberry Pi 4 (a Pi 2 would probably do too) with Ubuntu Server (we used 20.04).
* Arduino Uno.
* Arduino CNC Shield (v3.0.0 will do, improved functionality of GRBL is enabled with later versions), stepper drivers, and two capacitors in the 100 uF range.
* A "Gilson-style" p200 micropipette.
* Any CNC or 3D printer hardware (i.e. frames, guides, threaded rods or pulleys, steppers, limit switches, 3d printed parts, bearings, etc. TODO: make a BOM).
* Power supply (at least 12 V, steppers are best driven at just below the maximum voltage rating of the driver, AFAIK).
* Tips, tube racks, tubes, reagents, etc.

### Software

Raspberry Pi requires: Node, MongoDB, python3, and R (optional, for PCRmix protocol builder).

Arduino requires: GRBL v1.1h

Your computer requires: a modern browser.

## Architecture

1. The GUI generates "workspaces" by using platforms as "templates" and filling the `content` of them regarding user definitions in the UI.
2. Then the user defines a "protocol" for that workspace (a sequence of operations over objects in the workspace). The GUI translates the protocol into "High Level Commands" as representations of each operation or group of operations.
3. The "protocol2gcode" python3 module interprets these commands sequentially, and streams the necessary GCODE to the hardware firmware (modified GRBL 1.1h).

Templates for the definitions (of workspaces, protocols, and platforms) are in JSON format. Those must be imported to your local mongodb server (learn more at the [protocol2gcode](#protocol2gcode) section).

## Modules

### GUI

Express.js webapp to create workspaces, contents and protocols.

### protocol-builder

Library that interprets the user input and generates protocol.json files.

### workspace-builder

Library that interprets the user input and generates workspace.json files.

### protocol2gcode and gerbil_interface

#### protocol2gcode

Library that interprets protocol files and generate/stream GCODE to grbl.

After the GUI defines workspace, platforms and protocol, it saves all elementos it in the mongodb database. Then, it calls this python library to interpret it, and generate/stream the GCODE to grbl.

See protocol2gcode/README.md and defaults/README.md for instruction on setting up testing without the GUI, using the default JSON templates.

#### gerbil_interface

The geril python 3 module was included for testin. It seems promising!

## Firmware

GRBL was configured in "gantry" mode: two independent steppers and end stops.

## Hardware

### Electronics

Arduino UNO with CNC Shield 3.0 (clone).

Modifications (TODO: obsolete):

  * The Y axis is cloned to the A axis. Jumper pins are setup accordingly (gantry squaring is not supported at the same time as variable spindle on this CNC shield v3.0).
  * D12 and D11 were exchanged by disconecting pins on the shield. Using two short jumper wires, the pins on the Arduino were connected to the correct pins on the shield.
  * A 10 uF capacitor was connected between RESET and GND. This was necessary to prevent a GRBL reset when `pyserial` reconnects to the Arduino. There might be a software way to fix this, but I could not get it to work (see https://github.com/gnea/grbl/issues/160 ).
  * A servo was connected to the variable spindle PWM output pin (D11).

### Structure and Mechanics

Our own designs for parts are still being tested, find them in the "models" directory.

Since the micropipette does not need as much structural stiffness in the XYZ axes as a CNC machine, any CNC or 3D printer structure would work just fine.

I other words, you are not bound to use our models, except perhaps for the pipette tool adapter (also refered to as the "S axis" elsewhere).

# In action

We will eventually post some eye candy here.

![here comes the airplane!](doc/bot.gif)
