# Pipettin' GRBL

Pipetting robotware for laboratory protocol automation.

## Project objective

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

> Proper documentation to build this yourself is not yet ready, let us know if you wish to get help, or help out :)

![mender1_cdnm_mazinger](doc/media/pics/21_04-en_el_labo/IMG_7441.JPG)

# Guia de usuario

Aca no explicaria nada de la arquitectura ni de los modulos que intervienen). Este deberia ser el readme.md principa.

# Introduccion sin tanto tecnicismo

# Guia Instalacion de imagen raspberry y quemado de arduino

Restore our SD card image:

```
gunzip --stdout pipettin_pi.img.gz | sudo dd bs=4M of=/dev/YOUR_SD_CARD_DEVICE
```

Details at [raspberrypi.org](https://www.raspberrypi.org/documentation/linux/filesystem/backup.md).

# Calibracion de pipeta

# Calibracion de workspace

# Manual de GUI

# Assembly guide

Find assembly and setup instructions at [ASSEMBLY](ASSEMBLY.md).

# Contributing and Development

Find design and functional details at [DEVELOPMENT](DEVELOPMENT.md).

# Credits

* Nicolás (project developer)
* Facundo (project developer)
* The developers of GRBL, and the greater open source community.
* The [reGOSH](https://regosh.libres.cc/en/home-en/) free tech, latin-american network!
