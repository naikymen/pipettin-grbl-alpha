En general se depositó más volumen al cargar 5% extra, aunque es menos marcado/seguro a volumen bajo.

Todas las diferencias se corrieron hacia arriba, mostrando el efecto de "cargar de menos".

Sin embargo:

* Se ve una tendencia a depositar "de más" a 150 uL. Pero el error está dentro del 2% y es razonable. Hay que chequear que no sea sistemático.
* Cargar 5% de mas **a 20 uL** no corrigió notablemente el error. Sigue cargando de menos aparentemente.

Tengo algunas interpretaciones:

* Hay un problema que hace que se cargue de menos a menos volumen, y de más a mayor volumen. Cargar 5% de más solo hizo que se corra para arriba.
* Cargar de más es la situacion analoga al pipeteo en serie:
  * Entonces tiene sentido que cargar 5% de más haya arreglado el error de pipeteo en paralelo a 50 uL (el pipeteo en serie fue 40 uL, ver `21-06-15-p200-calib`).
* El tip se moja un poco, por lo que se pierde alguito siempre:
  * Entonces cuando el tip se moja más al cargar más, también se pierde más por mojar el tip.
  	* ¿Las pipetas están calibradas para compensar esto? En ese caso deberia suceder que por cada 1uL pipeteado, se agregue un pelín extra. Cuando baja, baja también de más, pero usualmente no importa porque se usa hasta el segundo tope (i.e., siempre se baja del todo). Pero si fuera el caso, el pipeteo reverso siempre tiraría de más (y es una práctica recomendada por Gilson). Queda pendiente chequear.
* Puede ser que n=2 sea demasiado bajo y esté interpretando el ruido.
  * En ese caso, deberia hacer n=5 y cubrir mejor el volumen. 5x5=25 suena razonable para hacerlo una vez. Pero no dos veces... alta fiaca.
  * Para hacer ese exp *quizas* deberia fijar el volumen extra que se pipetea en vez de usa 5% fijo, o usar 2% fijo...
  * Debería hacer más pruebas a 20 uL para saber que pasa ahí. Y a los demás también en realidad, pero como ese es el que menos cambió y el que menos probé vale empezar por ahí.
  * Igual, la gente sabe que las pipetas tienen más error en volumenes bajos... pero quisiera evitar que se pipetee sistematicamente menos (o sea que el error sea 0 en promedio).


También es cierto que la pipeta arrancaba un porquito más alta en cada pipeteo (porque se tomaba 5% de mas, pero ese extra no se bajaba). No se si esto afecta en algo.
