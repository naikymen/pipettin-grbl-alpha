# protocol2gcode

This python3 module works as three things:

* Interpreter: loads "protocol" actions and "platform" and "workspace" objects from MongoDB, defined previously through the GUI.
* Slicer: parses "actions" and generates "GCODE" for the protocol.
* Driver: controls GRBL, the pipette motor and the tip-eject servo motor. Sends commands to the machine (either from a predefined task/protocol in the mongo database or from a basic "interactive" interpreter).

## Commands: GCODE and Pseudogcode

### GCODE

"Vanilla" GCODE passed on to GRBL to move the XYZ axis.

The spindle `M3` command is used to eject tips (see electronics readme):

  * Eject: `M3 S20`
  * Retract: `M3 S150`

### Pseudogcode

Defined at `driverGcodeSender2.py`.

Used by the intepreter to move the pipette "P" axis:

  * `Phome;2` home the pipette and retract 2 mm away from the limit switch.
  * `Pmove;5` displace the pipette 5 mm
  * `Pmove;-5` displace the pipette -5 mm

It also supports a "wait" command:

  * `Wait;2` waits 2 seconds before parsing next line in the protocol.

The prefixes used (stuff beforethe semicolon) can be overriden.

## Dependencies

`sudo apt install python3-pip`

`pip3 install pyserial pigpio rpi.gpio`

`pip3 install pymongo==3.4.0`

La versión 3.10 no se lleva bien con mongodb disponible en los repositorios de Raspbian.

`sudo apt install pigpio`

`pip3 install python-socketio`

Note: installing bare 'socketio' may not work (https://github.com/miguelgrinberg/python-socketio/issues/264#issuecomment-518011401).

Note: if you find errors using "pip" to install the package in arch, try `sudo pacman -S python-socketio`

### pigpio and 64-bit OSes

There are some kernel problems. They were suposedly fixed in V71 or even before that, but i couldnt get it to work in Ubuntu Server 20.04 for RPi 4. The proposed solution involved:

  sudo nano /boot/firmware/cmdline.txt

Adding at the end of the line: `iomem=relaxed strict-devmem=0`

See: https://github.com/joan2937/pigpio/issues/259

## Usage

### Dry run

Useful for debugging.

```bash
sudo pigpiod
python3 main.py --protocol "Simple Protocol" --dry
```

### Stream full protocol interactively

Useful for debugging.

```bash
sudo pigpiod
python3 main.py --protocol "Simple Protocol" --interactive
```

### Stream full protocol

```bash
sudo pigpiod
python3 main.py --protocol "Simple Protocol"
```

## Testing

### Using minicom to interface with GRBL directly

minicom can be used as a "serial monitor" from the linux CLI:

```bash
minicom -D /dev/ttyACM0 -b 115200
```

Notes:

* Your keystorkes will not be echoed.
* To exit minicom, press "Ctrl+A" and then "Z".
* The Arduino may be unresponsive in some cases (for example, after asking for a reset; i.e. `[MSG: Reset to continue]`).

### GRBL-only testing

On a PC, the `GPIO` and `pipgio` libraries may not be available.

In which case, "mock" objects are imported from `dummyGPIO.py`.

This allows the code to send `GCODE` requiring only:

* An arduino with GRBL on it.
* Editing `python test_norpi.py` to your testing needs.

### Headless testing pre-requisites

To test this without the GUI, you must setup and populate the database with valid workspaces, protocols and platforms.

Briefly:

Install and start `mongod` on your computer.

Import the JSON files with' `mongoimport`, as specified by the `defaults/README.md` file.

# TO-DO

## Jogging

See:

  * https://github.com/vlachoudis/bCNC/blob/master/bCNC/controllers/GRBL1.py
  * https://github.com/gnea/grbl/wiki/Grbl-v1.1-Jogging
