####### REP 1 ####

datos <- readODS::read_ods("data/21-09-06-p200/incremental_dos_en_serie.ods")
datos$diferencia <- datos$Pesado
datos$Vol <- datos$Esperado
datos$clase <- "serie"
# datos$rownum <- 1:nrow(datos)

datos$error <- datos$Esperado - datos$Pesado

library(ggplot2)

ggplot(datos) +
  geom_point(aes(x = Vol, y = abs(diferencia), color = clase, shape = as.factor(sign(diferencia)) )) +
  geom_hline(aes(yintercept = Vol)) +
  geom_hline(aes(yintercept = Vol-1), color = "gray", linetype = 2) +
  geom_hline(aes(yintercept = Vol+1), color = "gray", linetype = 2) +
  ggtitle("Masas del pipeteo en serie", "Targets en lineas horizontales +/-1 uL") + theme_minimal() 

ggplot(datos) +
  geom_point(aes(x = as.factor(Indice), y = error, color = as.factor(Esperado), group = Serie)) +
  geom_line(aes(x = as.factor(Indice), y = error, color = as.factor(Esperado), group = Serie)) +
  ggtitle("Errores del pipeteo respecto al orden en la serie") + theme_minimal() 


