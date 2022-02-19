library(ggplot2)

datos <- read.csv("data/21-06-15-p200-calib/21-06-15-p200-calib_1.csv")
datos$diferencia <- (datos$peso_final - datos$peso_inicial)*1000
# datos$rownum <- 1:nrow(datos)

ggplot(datos) +
  geom_point(aes(x = series_index, y = diferencia, color = grupo)) +
  geom_hline(aes(yintercept = Vol)) +
  ggtitle("Pipeteo de 40ul en serie y paralelo", paste(
          "No encuentro razon para la correlacion con \nel orden de pipeteo"))

ggsave("results/21-06-15-p200-calib/21-06-15-p200-calib_1-por_orden_pipeteo.png")

ggplot(datos) +
  geom_boxplot(aes(x = grupo, y = diferencia, color = grupo), fill=NA) +
  geom_point(aes(x = grupo, y = diferencia), fill=NA) +
  geom_hline(aes(yintercept = Vol)) +
  ggtitle("Pipeteo de 40ul en serie y paralelo", paste(
          "El pipeteo en paralelo dio consistentemente menos"))

ggsave("results/21-06-15-p200-calib/21-06-15-p200-calib_1-por_grupo.png")

###### segunda tanda reusando tubos anteriores #####

# CONCLUSION
# El ultimo de la serie (hasta el fondo de volumen) siempre da menos (3ul en la anterior, 4.5 ul en esta).
# Tambien da menos el pipeteo en paralelo, consistenemente (2ul en la anterior, 2.5 ul en esta).
# Hay que explicar:
# * ¿Por qué da menos el ultimo pipeteo en todos los casos?
# * ¿Por qué el ultimo pipeteo en serie es "peor" que los primeros (y unicos) pipeteos en paralelo?
# 
# A mi ojo, siempre observé que los tips siempre quedaban vacíos. No habia 2ul en los tips ni ahi.
# Eso significa que en todos los pipeteos en paralelo "tomó" de menos.
# Ese efecto no se modificó bajando el s_retract de 17 a 16 (en commanderTest.py).
# ¿Puede ser un poco de backslash?
# 
# Tengo que pensar...
# 

datos <- read.csv("data/21-06-15-p200-calib/21-06-15-p200-calib_2.csv")
datos$diferencia <- (datos$peso_final - datos$peso_inicial)*1000
# datos$rownum <- 1:nrow(datos)

ggplot(dplyr::filter(datos, Vol > 0)) +
  geom_point(aes(x = series_index, y = diferencia, color = grupo)) +
  geom_hline(aes(yintercept = Vol)) +
  ggtitle("Pipeteo de 40ul en serie y paralelo", paste(
    "Solo el ultimo de 'serie' dio visiblemente menos\n",
    "sin embargo parece que hay efecto global."))

ggsave("results/21-06-15-p200-calib/21-06-15-p200-calib_2-por_orden_pipeteo.png")

ggplot(dplyr::filter(datos, grupo=="serie")) +
  geom_point(aes(x = series_index, y = diferencia, color = grupo)) +
  geom_hline(aes(yintercept = Vol)) +
  ggtitle("Pipeteo de 40ul en serie", paste(
    "Solo el ultimo de 'serie' dio visiblemente menos\n",
    "sin embargo parece que hay efecto global."))

ggsave("results/21-06-15-p200-calib/21-06-15-p200-calib_2-por_orden_pipeteo-solo_serie.png")

ggplot(dplyr::filter(datos, grupo=="paralelo")) +
  geom_point(aes(x = series_index, y = diferencia, color = grupo)) +
  geom_hline(aes(yintercept = Vol)) +
  ggtitle("Pipeteo de 40ul en paralelo", paste(
    "El ultimo es el de volumen cero, esta bien\n",
    "Parece que da consistentemente menos."))

ggsave("results/21-06-15-p200-calib/21-06-15-p200-calib_2-por_orden_pipeteo-solo_paralelo.png")

ggplot(dplyr::filter(datos, Vol > 0)) +
  geom_boxplot(aes(x = grupo, y = diferencia, color = grupo), fill=NA) +
  geom_point(aes(x = grupo, y = diferencia), fill=NA) +
  geom_hline(aes(yintercept = Vol)) +
  ggtitle("Pipeteo de 40ul en serie y paralelo", paste(
          "El pipeteo en paralelo da consistentemente menos otra vez"))

ggsave("results/21-06-15-p200-calib/21-06-15-p200-calib_2-por_grupo.png")

