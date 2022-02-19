datos <- read.csv("data/21-06-01-p200-calib/calib_p200-21_06_01.csv")
datos$diferencia <- datos$peso_final - datos$peso_inicial
datos$Vol_ml <- datos$Vol / 1000
datos$rownum <- 1:nrow(datos)

library(ggplot2)
ggplot(datos) +
  geom_point(aes(x = rownum, y = diferencia, color = as.factor(Vol_ml))) +
  geom_hline(aes(yintercept = Vol_ml))


library(dplyr)
datos %>% filter(Vol<100) %>% 
ggplot() +
  geom_smooth(aes(x = Vol_ml, y = diferencia), method = "lm", color = "black") +
  geom_point(aes(x = Vol_ml, y = diferencia, color = as.factor(Vol_ml))) +
  geom_abline(slope = 1, intercept = 0)

