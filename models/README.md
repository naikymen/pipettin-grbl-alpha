TODO: reorganizar este readme.

TODO: agregar info de modelos pasados a FreeCAD bajo `modelos_ejez_Z_y_S/basic_parts_freecad/`.

# Sujetador Jeringas y Pipetas

Sujetador Jeringa CNC Stepper.stl en modelos_ejez_Z_y_S/

Diseño en TinkerCAD para el "eje pipeteador" que usa:

  * Una jeringa
  * Stepper NEMA 17
  * Varillas de 8 mm
  * Varilla roscada de 8 mm con tuerca.
  * Tuercas y tornillos M3 / varilla roscada y tuercas de 3 mm

Link: https://www.tinkercad.com/things/gWPShCd3e0L-sizzling-lappi-borwo/edit

## Requires

  * `topeJeringa1mL` en modelos_pipetas_jeringas/

# topeJeringa1mL

Diseño en FreeCAD para la "T" en la parte de arriba del émbolo de una jeringa de 1 mL.

Marca "Bremen", marcada como: "Tuberculina 1mL con aguja 0.5 x 15 mm 25Gx5/8".

# Otro modelo

https://www.thingiverse.com/thing:1684481

https://www.tinkercad.com/things/aL2rLg0KME9

# Meshroom folders

Photogrammetry test, to digitize pipettes.

https://www.youtube.com/watch?v=1D0EhSi-vvc

https://meshroom-manual.readthedocs.io/en/latest/tutorials/sketchfab/sketchfab.html

# Notas

## Pipette tip dimensions

https://www.fts.co.nz/image/data/PDF/Pipette%20Tips.pdf

  * p1000 ~ 70 mm
  * p200 ~ 50 mm
  * p20 ~ 37-46 mm

Por lo tanto el eje Z debería poder viajar al menos 70 mm.

El eje Z del CNC solamente tiene 30 mm de viaje aproximadamente.

En un caso razonable, en el que haya un falcon de 50 en el workspace para usar con una p1000, el recorrido mínimo para poder pipetear todo debería ser 140 mm.
