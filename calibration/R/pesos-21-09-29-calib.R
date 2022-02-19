####### REP 1 ####

datos <- readODS::read_ods("data/21-09-29-p200/serie_y_paralelo.ods")
datos$diferencia <- datos$Pesado
datos$Vol <- datos$Esperado
# datos$rownum <- 1:nrow(datos)

datos$error <- datos$Esperado - datos$Pesado

library(ggplot2)

ggplot(datos) +
  geom_point(aes(x = Vol, y = abs(diferencia), color = Clase, shape = as.factor(sign(diferencia)) )) +
  geom_hline(aes(yintercept = Vol)) +
  geom_hline(aes(yintercept = Vol-2), color = "gray", linetype = 2) +
  geom_hline(aes(yintercept = Vol+2), color = "gray", linetype = 2) +
  ggtitle("Masas del pipeteo en serie", "Targets en lineas horizontales +/-3 uL") + theme_minimal() 

ggplot(datos) +
  geom_point(aes(x = as.factor(Indice), y = error, color = as.factor(Serie), group = Serie)) +
  geom_line(aes(x = as.factor(Indice), y = error, color = as.factor(Serie), group = Serie)) +
  ggtitle("Errores del pipeteo respecto al orden en la serie") + theme_minimal() 

# ggsave("results/21-09-29-p200-calib/p200_4serie_2par.png")

ggplot(datos) +
  geom_point(aes(x = as.factor(Indice), y = 100*error/Esperado, color = as.factor(Serie), group = Serie)) +
  geom_line(aes(x = as.factor(Indice), y = 100*error/Esperado, color = as.factor(Serie), group = Serie)) +
  ggtitle("Errores del pipeteo respecto al orden en la serie", "Porcentual respecto a esperado") + theme_minimal() 

# ggsave("results/21-09-29-p200-calib/p200_4serie_2par_percent.png")
