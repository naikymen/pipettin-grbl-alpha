# Platforms

These are virtual objects with properties representing physical objects in the workspace,
such as tip boxes and tube racks.

## Positional calibration

Positional calibration.

Repeat each time the platforms are moved.

## XY calibration

For any platform:

1. Home the machine XYZ.
2. Move the robot to the content at corner of the platform, and lower the pipette until it is a few millimeters over the objects (tips or tubes).
3. Adjust the physical platform such that it center point is precisely aligned with the pipette's shaft. 
4. Move the pipette to the content at the oposite corner, and repeat the alignment (previous step). Be careful, you may lose alignment of the other corner in the process.
5. Just in case, repeat these steps once again.

## Z calibration

Usage height calibration.

### Tip box

1. Home the machine XYZ.
2. After the XY calibration, lower the pipette until the red LED of the tip sensor turns off.
3. Register the new height shown in the coordinates.
4. Edit the tip box platform properties, setting `defaulBottomPosition` and `defaultBottomPosition` equal to that value.

### Tip offset

1. Home the machine's XYZ.
2. Place a tip on the pipette (until the red LED of the tip sensor turns off).
3. Move the pipette over some stiff object, and lower it until it barely touches it.
4. Register the Z position shown in the panel (`Z_tip`).
5. Move the pipette up, remove the tip, and repeat step 3.
6. Register the Z position shown in the panel (`Z_shaft`).

Note: this information is useful in general, but it is not currently used by the Tube rack path calculations.

### Tube rack

1. Home the machine's XYZ.
2. Place the tube rack with a tube in one of the slots.
3. Place a tip on the pipette (until the red LED of the tip sensor turns off).
4. Move the pipette over the tube, and lower it until the tip is barely above the bottom, but does not touch it (if it does, raising the pipette 0.5 mm should be enough).
5. Register the Z position shown in the panel.
6. Edit the tube rack platform properties, setting `p200LoadBottom` equal to the registerd value (add 0.5 if unsure).

Note: this is the simplest way to callibrate pipetting height. Using the tip offest will surely help with other platforms.
