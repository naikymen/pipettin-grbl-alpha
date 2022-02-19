datos <- read.csv("data/21-03-16-calib/pesos.csv")
datos$diferencia <- datos$peso_final - datos$peso_inicial

library(ggplot2)
ggplot(datos) +
  geom_point(aes(x = orden_en_secuencia, y = diferencia, color = as.factor(vol)))

datos <- read.csv("pesos2.csv")
datos$diferencia <- abs(datos$peso_final - datos$peso_inicial)
ggplot(datos) +
  geom_point(aes(x = orden_en_secuencia, y = diferencia, color = as.factor(vol)))
