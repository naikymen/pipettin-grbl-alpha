# Pipettin' GRBL

Pipetting robotware for laboratory protocol automation.

This repository contains hardware design files and software, 
licenced under the [CERN-OHL-S licence](https://github.com/naikymen/pipettin-grbl-alpha/blob/master/HARDWARE_LICENCE.txt) 
and the [GNU GPLv3 licence](https://github.com/naikymen/pipettin-grbl-alpha/blob/master/SOFTWARE_LICENCE.txt), respectively.

![mender1_cdnm_mazinger](doc/media/pics/21_04-en_el_labo/IMG_7441.JPG)

> Pardon our _castellano_ :)

# Introduction

<!-- sin tanto tecnicismo -->

Video overview available at [YouTube](https://www.youtube.com/watch?v=5_eDGsb4E6M&list=PLSqqZBTIQ_dz2dSU0l852d4ZE4sjo2JjA):

[![youtube playlist](https://user-images.githubusercontent.com/3259326/154876955-560acf31-f670-4b91-8ee6-504c9dda07c8.png)](https://www.youtube.com/watch?v=5_eDGsb4E6M&list=PLSqqZBTIQ_dz2dSU0l852d4ZE4sjo2JjA)

# User guide

<!-- Aca no explicaria nada de la arquitectura ni de los modulos que intervienen). Este deberia ser el readme.md principa. -->

## Web GUI guide

<!-- Manual de GUI -->

## Machine callibration

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

### Workspace and platforms

<!-- Calibracion del XYZ de los objetos en la mesa -->

# Software installation

## Raspberry Pi image

<!-- Guia Instalacion de imagen raspberry -->

Restore our SD card image:

```
gunzip --stdout pipettin_pi.img.gz | sudo dd bs=4M of=/dev/YOUR_SD_CARD_DEVICE
```

Details at [raspberrypi.org](https://www.raspberrypi.org/documentation/linux/filesystem/backup.md).

## Arduino firmware

<!-- Guia Instalacion de GRBL en Arduino UNO -->

# Assembly guide

Find assembly and setup instructions at [ASSEMBLY](ASSEMBLY.md).

# Contributing and Development

Find design and functional details at [DEVELOPMENT](DEVELOPMENT.md).

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
