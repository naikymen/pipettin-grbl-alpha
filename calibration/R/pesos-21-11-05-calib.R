####### REP 1 ####

results_dir <- "results/21-11-05-p200-calib/"
results_file <- "data/21-11-05-p200/serie_x4_triplicado.ods"

datos <- readODS::read_ods(results_file)
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
  geom_hline(aes(yintercept = Vol-1), color = "gray", linetype = 2) +
  geom_hline(aes(yintercept = Vol+1), color = "gray", linetype = 2) +
  
  facet_wrap(~as.factor(Esperado), scales = "free") + 
  
  ggtitle("Masas del pipeteo en serie", "Targets en lineas horizontales +/-1 uL") + theme_minimal()

dir.create(results_dir)
ggsave(paste0(results_dir,"/","pruebas_serie.png"))

# En este probé:
# Remover el backslash compensation.
# Hacer que tome de más al inicio (como ya hace) pero que luego largue un poquito (1 uL). Quizas eso evite el error grande al inicio.

# Resultado
# El error al inicio desapareció :)
# Pero el último pipeteo sigue largando de menos.
# Estimo que el problema es el mismo: tensión superficial en el tip a bajo volumen.
# Algo que noté es que casi no quedaba volumen en el tip al terminar el pipeteo. Aunque a veces quedaba un poco más, a veces era casi nada.
# Hay dos cosas importantes ahi: 
#  * No quedarme sin volumen por el tema de "mojar el tip" (cosa que no parece suceder).
#  * Si es un tema de tension superficial, seguramente sea más difícil sacar volumen cuando queda solo 1 uL en el tip.
# Otra cosa importante es que en los primeros puntos pieptea consistentemente de más, como 0.5 uL.
# Ya casi no hay backslash compensation que explique eso, y no debería triggerearse en el pipeteo en serie, así que descartado.
# Sin embargo, explica por qué queda tan poco volumen en el tip al final del pipeteo.

# Para la próxima
# * Identificar la causa del tema de sobre-pipeteo de 0.5 uL en los primeros 3 puntos.
#   Quizás si arreglo eso, no tenga que probar lo siguiente.
# * Probar aumentar el s_retract para que queden más volumen al final de la serie.
# * Probar agregar lógica para que pipetee 1 uL de más si el volumen final en el tip va a ser muy bajito (como al final de la serie).

# CORRECCIÓN / FE DE ERRATA
# No se estaba aplicando el cambio de bajar a 0.1 uL el backslash correction.
# Eso, además, solo aplicaba al primer punto después del back-pour, entonces no tuvo mucho efecto.
# En conclusión, la mejora observada se debe principalmente al back-pour correction (que es anti backslash en realidad, pero no mecánico, sino "fluídico").
