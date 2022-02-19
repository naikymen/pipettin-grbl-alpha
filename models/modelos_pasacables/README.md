# Concept

* https://en.wikipedia.org/wiki/Cable_carrier

# Thingiverse models

* Esta tiene infinitos likes, parece que es la que va: https://www.thingiverse.com/thing:1078216
* https://www.thingiverse.com/thing:2125076
* https://www.thingiverse.com/thing:204791
* Pero me gustó más esta: https://www.thingiverse.com/thing:4375470

## Chosen model

Thing 4375470 (chain_link_v2-Clip.scad) at https://www.thingiverse.com/thing:4375470

## Model issues

We tried tolerances 0.1, 0.2 and 0.3. Unfortunately all presented problems:

  * 0.1 was too small, and movement was impaired.
  * 0.2 and 0.3 were too loose, allowing bending of the chain in the wrong direction.

### Chain clip problem

The original clips fit too tight.

Placing the clip deforms the model a little so that the hinges move more freely.  A slowly deforming clip will eventually fail, and the hinges may become lodged again. So putting less stress on that part (i.e. by making it wider or ncreasing tolerance) seems prudent.

## Solution

Since no compromise in "tolerance" was good enough, we modified the OpenSCAD model to fit our needs:

  * Setting `under_angle=-4;` will fix the tolerance problem (line 29) producing chains that do not bend in the opposite direction.
  * Added a `clip_extra_width = 0.5;` and `clip_extra_tolerance=0.05` parameters to relax the clip a little (line 44 and 45).
  * several other patches are mentioned below...

### Patches and explanation

Setting `under_angle=-4;` in the original version of the model caused some weird artifacts to appear. We removed them by subtracting two cubes in the seemingly "right" places (lines 98 and 126).

Also, this setting made the base of the chain detach from the baseplane in the original model. While this might have been intentional, it has two problems:

  * Makes printing harder.
  * Causes the links to lock less tightly, in a way that the "under angle" is less than expected (i.e. when setting `under_angle=-4;` you actually get less).

To fix this I added two blocks of the right height at the base of each side of the chain module (line 66 and 67). 

----

Added a 0.005 offset and enlarged one of the cubes in the `outline` module, which removed a strange visual artifact (line 73).

----

The clip tolerance was applied to the slot, but not to the clip. While this may have been intentional now there is a `clip_extra_tolerance=0.05` setting for that (line 45; the default used to be 0).

----

There was a small notch in the material that appears when setting `under_angle=-4;`. This is due to rotation of the cube at line 172. I moved the rotation function so that it only affects the `middle_0` module, and not the cube at line 172.

## Printing notes

An accurate first layer is important in this model to prevent bending of the chain in the wrong direction.

Squashed frist layer or elephants foot must be avoided. If the first layers print wider than expected, the hinges will become stuck on assembly. On the other hand, if they are smaller the chain will bend in the wrong direction more easily.

Proper calibration of the first layer height and/or using elephant's foot compensation may be important.

## Post-printing

Adding some graphite dust can help with lubrication and extend durability of the hinges.

# Changelog

## v0.1

Working cable carrier model.

## v0.2

Incremente el "underangle" un poco. Las orugas más largas se doblan un poco hacia adentro todavía :/

Pasó de -4 a -4.5 en el archivo openscad.

