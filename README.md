# Pipettin' GRBL

Pipetting robotware for laboratory protocol automation.

This repository contains hardware design files and software for a test prototype. 
Hardware is licenced under the [CERN-OHL-S](https://github.com/naikymen/pipettin-grbl-alpha/blob/master/HARDWARE_LICENCE.txt) licence 
and software under the [GNU GPLv3 licence](https://github.com/naikymen/pipettin-grbl-alpha/blob/master/SOFTWARE_LICENCE.txt) licence.

![mender1_cdnm_mazinger](doc/media/pics/21_04-en_el_labo/IMG_7441.JPG)

> Pardon our _castellano_ :)

# Introduction

<!-- sin tanto tecnicismo -->

Video overview available at [YouTube](https://www.youtube.com/watch?v=5_eDGsb4E6M&list=PLSqqZBTIQ_dz2dSU0l852d4ZE4sjo2JjA):

[![youtube playlist](https://user-images.githubusercontent.com/3259326/154876955-560acf31-f670-4b91-8ee6-504c9dda07c8.png)](https://www.youtube.com/watch?v=5_eDGsb4E6M&list=PLSqqZBTIQ_dz2dSU0l852d4ZE4sjo2JjA)

# User guide

<!-- Aca no explicaria nada de la arquitectura ni de los modulos que intervienen). Este deberia ser el readme.md principa. -->

> TO-DO

## Web GUI guide

<!-- Manual de GUI -->

> TO-DO

## Machine calibration

Callibration instructions before protocol run.

### Pipette

<!-- 
Calibracion de pipeta:

- Relacion Volumen-deplazamiento
- Tip probe
- Setup de las constantes en el driver (retraction, etc.)
- Setup de las correcciones en el driver (pipeteo de mas / de menos, etc.)
- Protocolo de calibracion con balanza analítica.
-->

> TO-DO

### Workspace and platforms

<!-- Calibracion del XYZ de los objetos en la mesa -->

> TO-DO

# Software installation

## Raspberry Pi image

<!-- Guia Instalacion de imagen raspberry -->

Requirements:

* The system's [image](https://drive.google.com/drive/folders/1sQWp9x0S_202jgzFJBe-YqoJQlnTlY16?usp=sharing).
* 64 GB micro SD card.
  * If you have a smaller SD card, try [trimming](https://superuser.com/a/610825) the image's filesystem before flashing.

Restore our SD card image using `dd` and `gunzip` from a terminal:

```
# Replace "YOUR_SD_CARD_DEVICE" with your SD card's actual device name (you may use "lsblk" to find it).
gunzip --stdout pipettin_pi.img.gz | sudo dd bs=4M of=/dev/YOUR_SD_CARD_DEVICE
sync
```

To create the compressed filesystem backup, we used:

```
# Replace "sda" with your SD card's actual device name (you may use "lsblk" to find it).
sudo dd bs=4M status=progress if=/dev/sda | gzip > pipettin_pi.img.gz
sync
```

Details at [raspberrypi.org archive](https://web.archive.org/web/20210419061127/https://www.raspberrypi.org/documentation/linux/filesystem/backup.md).

## Arduino firmware

<!-- Guia Instalacion de GRBL en Arduino UNO -->

> TO-DO

# Assembly guide

Find assembly and setup instructions at [ASSEMBLY](ASSEMBLY.md).

> TO-DO

# Contributing and Development

Find design and functional details at [DEVELOPMENT](DEVELOPMENT.md).

> TO-DO

# Credits

Original development by Nicolás and Facundo:

* The web UI.
* Models for the the CNC frame and pipette actuators.
* CNC and pipette drivers.

We are very thankful to:

* The developers of GRBL, and the greater open source community.
* The [reGOSH](https://regosh.libres.cc/en/home-en/) free tech, latin-american network!

# About this project

## Project objectives

To make a liquid handling robot which is:
- easy to use,
- fully open source,
- highly documented, 
- modular in design,
- minimal in cost,
- very hackable,
- and integrates well with other labware projects.

## Project status

We've reached "alpha" status, and are currently applying for funding to fully document this project.

Our bot can:

* Be programmed using a very nice web UI.
* Place tips, load and dispense liquid solutions, and discard tips.
* Prepare combinatorial PCR mixes with a reasonably optimized automatic planner.

> Proper documentation to build this yourself is not yet ready, let us know if you wish to get help, or help out :)
