####### REP 1 ####

datos <- readODS::read_ods("data/21-10-01-p200/serie_y_paralelo.ods")
datos$diferencia <- datos$Pesado
datos$Vol <- datos$Esperado
# datos$rownum <- 1:nrow(datos)

datos$error <- datos$Esperado - datos$Pesado

library(ggplot2)

ggplot(datos) +
  geom_line(aes(x = Orden, 
                y = Pesado, 
                color = as.factor(Serie),
                group = as.factor(Serie)
                )) +
  geom_hline(aes(yintercept = Vol)) +
  geom_hline(aes(yintercept = Vol-2), color = "gray", linetype = 2) +
  geom_hline(aes(yintercept = Vol+2), color = "gray", linetype = 2) +
  
  facet_wrap(~as.factor(Esperado), scales = "free") + 
  
  ggtitle("Masas del pipeteo en serie", "Targets en lineas horizontales +/-3 uL") + theme_minimal()

ggsave("results/21-10-01-p200-calib/pruebas_serie.png")

# Usando 5 repeticiones se ve que el error es más alto en la primera y en la ultima.
# El problema de la primera puede ser debido a la corrección de backslash que le puse (agrega volumen de más al cambiar de dirección, 0.5 uL en este caso ).
# El de la última no sé qué es... volumen queda en el tip, así que ese no es el problema.
# No se me ocurre qué cosa de software podría estar causando eso.

# En el proximo deberia probar:
# Remover el backslash compensation.
# Hacer que tome de más al inicio (como ya hace) pero que luego largue un poquito. Quizas eso evite el error grande al inicio.
# Jugar con el setting "s_retract" y ponerlo un poco más arriba.
# Jugar con el setting de over-draw con tip nuevo "extra_draw_volume", para que tome un poco más y ver qué pasa.
## Eventualmente debería ser lo mismo que descartar la ultima repeticion en la serie (si fuera igual al volumen pipeteado por repeticion).
## En realidad no tengo tanta razon para sospechar de esto, porque siempre que miré quedaba volumen para largar en el tip.
## Por otro lado, el resorte del segundo tope no se llega a tocar con el "s_retract" actual. aunque mas resistencia a mayor compresion del resorte explicaria una leve tendencia general, no creo que seria tan marcada.
## Pero quien sabe, realmente no sé qué es lo que esta pasando con la tensión superficial en estos tips...


ggplot(datos) +
  geom_point(aes(x = Vol, y = abs(diferencia),
                 # color = clase, 
                 color = Orden, 
                 shape = as.factor(sign(diferencia)) )) +
  geom_hline(aes(yintercept = Vol)) +
  geom_hline(aes(yintercept = Vol-1), color = "gray", linetype = 2) +
  geom_hline(aes(yintercept = Vol+1), color = "gray", linetype = 2) +
  ggtitle("Masas del pipeteo en serie", "Targets en lineas horizontales +/-1 uL") +
  theme_minimal() + theme(legend.position = "none")

