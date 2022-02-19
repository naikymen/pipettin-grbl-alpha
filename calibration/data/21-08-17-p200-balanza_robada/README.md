## Conclusiones a ojo

* El `s_retract` parece afectar solo un poco el tema de "tomar de menos en la primera".
  * Para no perder más rango de volumen del que ya estaba perdiendo (180/200 uL tenía aprox.), deberia compensar levantando 20 uL la pipeta después de hacer homing.
* Puede tomar entre 1 y 3 uL de menos en la primera (pipeteando de a 20 uL) y suele tomar de menos tambien en la segunda (pipeteando de a 10 uL).
* Los pipeteos de cambio de direccion muestran que hay 0.5 uL de "backslash" aproximadamente.
* Al expulsar volumen, dio siempre de más, eso es consistente con esta parte del `actionInterpreter.py`:

```
            # Add 5% to a volume loading pipette displacement:
            if _action["args"]["volume"] > 0:
                _action["args"]["volume"] = _action["args"]["volume"]*1.05
```

Por lo tanto, estaba de más y se puede sacar (y lo saqué).

## Prueba con 20 uL de "anti homing-backslash"

No funcionó.

Conclusión: el problema está en cargar volumen en un tip vacío, respecto a cargar volumen en un tip que ya tiene líquido.

La compensación debe hacerse cada vez que se use un tip nuevo.

Juan Mucci tenía razón jaja. El día que lo vea de nuevo se la reconoceré.

¿Por qué será?

Coincide con que sistemáticamente tenga que preparar más PCR mix de la que voy a usar, como si la pipeta siempre tomara de más, y luego largara el volumen correcto.

Para el pipeteo repetido se toma bastante de más a propósito, y después se usa solo el primer tope.
Tiene sentido entonces hacer lo mismo para un pipeteo repetido/serial en el robot.

Para mí es sorprendente es que también haya que corregir esto para el pipeteo "normal" (o sea, no seriado).

Lo ultimo que hice, a ojo, fue pipetear de a 1uL con la p200 y paso algo bastante loco...

Toqué 3 veces el botón, asi que tome 3 uL en teoria. La balanza dice que tome solo ~ 1.9 uL. Eso es esperable dado lo que observe antes tomando de a 10 uL.

Lo sorprendente es que las primeras dos veces que toqué el botón, no cargó **nada**, y solo al tercer toque se lleno la puntita del tip con esos 1.9 uL.

Pero no es que no *pasó* nada en los primeros dos toques. Creo que son necesarios para "mojar" el tip por adentro, y vencer la tensión superficial del agua.
Eso tendría sentido si a agua no le gustara tanto mojar el plástico (i.e. que el plástico no sea tan hidrofílico).
Entonces tendría sentido pensar que los dos primeros toques son necesarios para hacer suficiente "vacío" para vencer la tension superficial del agua y meterla al tip.
Una vez que se vence, y el tip se moja un poco, 1.9 uL de agua suben de golpe.
Pero no suben 3 uL ¿por qué? tampoco estoy seguro.

Lo que acabo de notar es que otra p200 tiene el mismo tema: si subo el émbolo solo un poquito, el liquido no sube por el tip. Pero despues de moverlo un poquitin mas, sube bien.
Lo mismo pasa con la p2, tiene un poco de recorrido "muerto" donde subir el émbolo no carga nada de volumen, y un poquitin más hace que suba la cantidad correcta.
Re loco.

Ahora podria entender eso de que el tip "se moja" de otra manera: lo que se moja en un sentido problemático no solo las paredes del tip.
"Mojar" en este contexto quizás significaba mojar *el tip del tip*, es decir, la presion necesaria para vencer la tension superficial del agua (water bending?) y hacerla ingresar al tip.

Creo que no me cierra del todo: en teoria si uno pipetea normalmente (usando un tip una vez para pasar liquido de un tubo a otro) esto pasa, y el volumen cargado es menor al esperado.
Entonces la pipeta deberia cargar un poco de más siempre, para cargar correctamente. Pero despues al bajar la pipeta ¿se echaria lo mismo que se cargó? 
¿O deberia ser menos? por el tema de mojar las paredes del tip. Yo perdi volumen misteriosamente en los pipeteos seriados cuando hice ida y vuelta, asi que puede ser.
En ese caso la pipeta siempre deberia cargar de mas por dos razones: (1) esos 2-3 uL necesarios para que entre el liquido y (2) por lo que se mojan las paredes del tip.

Sin embargo, la p2 carga 0.2 uL sin tener este problema, y es con tips más chicos todavía. ¿estará corregida para eso? Así que no sé... tendría que probar poniendo una p2 en el robot.
Por lo pronto hay dos opciones: (1) no entiendo nada (2) las pipetas estan corregidas para contemplar este tema.

### Conclusión
 
La solución es obvia: cada vez que se pone un tip nuevo para pipetear agua, hay que tomar 2-3 uL de más al inicio, y después bajar lo que uno quiere pipetear.

Esa manera de pipeteo va a ser reproducible.

El trade-off es que siempre se toma solución de más (desperdiciando 3 uL cada vez). Pero eso era algo que ya me pasa con las mix para PCR.


