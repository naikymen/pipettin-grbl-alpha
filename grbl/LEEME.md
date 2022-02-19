# Pipetting GRBL firmware

Vanilla GRBL 1.1h should work fine unless you need to control a servo (which you do need to use the tip ejector).

## Usage

Import this directory as a library in the Arduino IDE. Use the "grbl upload" example to burn GRBL onto the Arduino UNO.

If you have already installed the 10uF capacitor across the reset/abort pins (to prevent reset on serial reconnect), you may need to remove it temporarily before uploading the frimware (or you may get some errors while doing so).

## Testing

You may interact with GRBL from a linux terminal using `minicom`. For example:

```bash
minicom -D /dev/ttyACM0 -b 115200
```

Try typing `?` to check GRBL's status, or `$$` and pressing enter to see its settings.

The python scripts offer a rudimentary interactive text-based interface, using the `--interactive` option. That one wraps the serial interface, and controls other parts of the machine (i.e. the tool/pipette axis).

## Modifications

All major modifications are on the hardware side, specially on the Arduino CNC Shield 3.0 clone.

*IMPORTANT*: `ENABLE_DUAL_AXIS` and `VARIABLE_SPINDLE` are incompatible in our setup (though in theory its not impossible to enable them simultaneously).

### Servo control via Variable Spnidle PWM

If using a servo motor on the spindle enable pin, enable variable spindle with `#define VARIABLE_SPINDLE` (at line 339 of `config.h`).

The spindle PWM frequency is altered in `cpu_map.h` to be compatible with a hobby servo. Using a 1024 prescaler in fast-mode PWM we get `~60 Hz` which worsk great for ejecting tips.

Note: we tried to use this for the pipette axis. But the servo was not precise enough, and had a "bounce" effect which cannot happen during pipetting.

Ver wiki:

  * https://wiki.frubox.org/proyectos/diy/cnc#controlar-un-servo-con-el-spindle

### Dual Y axis Gantry squaring

This is disabled in our build. Our A axis clones the Y axis.

If you have dual X or Y axis (ie, two independent steppers and threaded rods for one direction of movement) enable gantry squaring with `ENABLE_DUAL_AXIS`. Follow the official GBRL documentation for correct configuration and limit switch setup.

## Configuration notes

I advise not using `$1=255` as it does not seem to play nice with our testing hardware (with A4988 drivers).

The full configuration for our setup makes GRBL work in positive space coordinates with origin at X0 Y0 by setting the masks correctly and issuing the corresponding G92 command after homing.

We also needed to reverse the Y axis and the XT homing direction. This is because the web-based GUI uses that coordinate system (right and down are positive the directions) and because reversing the homing direction will leave the machine at this origin (it otherwise homes to max X/Y instead of min X/Y).
