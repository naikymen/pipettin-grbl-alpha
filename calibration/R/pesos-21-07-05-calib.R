
####### REP 1 ####

datos <- read.csv("data/21-07-05-p200-calib/calib_p200.csv")
datos$diferencia <- (datos$peso_final - datos$peso_inicial)*1000
# datos$rownum <- 1:nrow(datos)

library(ggplot2)
ggplot(datos) +
  geom_point(aes(x = Vol, y = abs(diferencia), color = clase, shape = as.factor(sign(diferencia)) )) +
  geom_hline(aes(yintercept = Vol)) +
  ggtitle("Pipeteo en paralelo pesando origen y destino", paste("rep2")) + theme_minimal() 

ggplot(datos) +
  geom_point(aes(x = as.factor(Vol), y = abs(diferencia) - Vol, color = clase, shape = as.factor(sign(diferencia)) )) +
  geom_hline(aes(yintercept = 0)) +
  ylim(c(-5,5)) +
  ggtitle("Pipeteo en paralelo pesando origen y destino", paste("rep2")) + theme_minimal() 

ggplot(datos) +
  geom_point(aes(x = as.factor(Vol), y = diferencia / Vol, color = clase, shape = as.factor(sign(diferencia)) )) +
  # Agregar target y error de 2%
  geom_hline(aes(yintercept = 1)) + geom_hline(aes(yintercept = 1+ 0.02), color="gray") + geom_hline(aes(yintercept = 1-0.02), color="gray") +
  geom_hline(aes(yintercept = -1)) + geom_hline(aes(yintercept = -1 -0.02), color="gray") + geom_hline(aes(yintercept = -1 + 0.02), color="gray") +
  ylim(c(-1.2,1.2)) +
  ggtitle("Pipeteo en paralelo pesando origen y destino", paste("rep2")) + theme_minimal()

####### REP 2 ####

datos <- read.csv("data/21-07-05-p200-calib/calib_p200_2.csv")
datos$diferencia <- (datos$peso_final - datos$peso_inicial)*1000
# datos$rownum <- 1:nrow(datos)

ggplot(datos) +
  geom_point(aes(x = Vol, y = abs(diferencia), color = clase, shape = as.factor(sign(diferencia)) )) +
  geom_hline(aes(yintercept = Vol)) +
  ggtitle("Pipeteo en paralelo pesando origen y destino", paste("rep2")) + theme_minimal() 

ggplot(datos) +
  geom_point(aes(x = as.factor(Vol), y = abs(diferencia) - Vol, color = clase, shape = as.factor(sign(diferencia)) )) +
  geom_hline(aes(yintercept = 0)) +
  ylim(c(-5,5)) +
  ggtitle("Pipeteo en paralelo pesando origen y destino", paste("rep2")) + theme_minimal() 

ggplot(datos) +
  geom_point(aes(x = as.factor(Vol), y = diferencia / Vol, color = clase, shape = as.factor(sign(diferencia)) )) +
  # Agregar target y error de 2%
  geom_hline(aes(yintercept = 1)) + geom_hline(aes(yintercept = 1+ 0.02), color="gray") + geom_hline(aes(yintercept = 1-0.02), color="gray") +
  geom_hline(aes(yintercept = -1)) + geom_hline(aes(yintercept = -1 -0.02), color="gray") + geom_hline(aes(yintercept = -1 + 0.02), color="gray") +
  ylim(c(-1.2,1.2)) +
  ggtitle("Pipeteo en paralelo pesando origen y destino", paste("rep2")) + theme_minimal()


####### REP 3 ####

datos <- read.csv("data/21-07-05-p200-calib/calib_p200_3.csv")
datos$diferencia <- (datos$peso_final - datos$peso_inicial)*1000
# datos$rownum <- 1:nrow(datos)

ggplot(datos) +
  geom_point(aes(x = serie, y = abs(diferencia), color = clase, shape = as.factor(sign(diferencia)) )) +
  geom_hline(aes(yintercept = Vol)) +
  geom_hline(aes(yintercept = Vol+1), color="gray", alpha = .5, size = 1.1) +
  geom_hline(aes(yintercept = Vol-1), color="gray", alpha = .5, size = 1.1) +
  geom_hline(aes(yintercept = Vol+0.02*Vol), color="gray", linetype=2, alpha = .5, size=1.1) +
  geom_hline(aes(yintercept = Vol-0.02*Vol), color="gray", linetype=2, alpha = .5, size=1.1) +
  ggtitle("Pipeteo en paralelo pesando origen y destino",
          paste("rep4", sep = "\n",
                "gris liso 1uL error, gris punteado 2% error.",
                "outliers removidos"
          )) + 
  theme_minimal() + facet_wrap(~Vol, scales = "free_y")

# ggsave("results/21-07-05-p200-calib/rep4.png")

ggplot(datos) +
  geom_point(aes(x = serie, y =  Vol - abs(diferencia), color = clase, shape = as.factor(sign(diferencia)) )) +
  geom_hline(aes(yintercept = 0)) +
  ylim(c(0,5)) +
  ggtitle("Pipeteo en paralelo pesando origen y destino",
          paste("rep4")) + 
  theme_minimal() + facet_wrap(~Vol, scales = "free_y")

ggplot(datos) +
  geom_point(aes(x = serie, y = diferencia / Vol, color = clase, shape = as.factor(sign(diferencia)) )) +
  # Agregar target y error de 2%
  geom_hline(aes(yintercept = 1)) + geom_hline(aes(yintercept = 1+ 0.02), color="gray") + geom_hline(aes(yintercept = 1-0.02), color="gray") +
  geom_hline(aes(yintercept = -1)) + geom_hline(aes(yintercept = -1 -0.02), color="gray") + geom_hline(aes(yintercept = -1 + 0.02), color="gray") +
  ylim(c(-1.2,1.2)) +
  ggtitle("Pipeteo en paralelo pesando origen y destino",
          # paste("rep3: la serie 4 tiene 5% extra de loading")) + 
          paste("rep4")) + 
  theme_minimal() + facet_wrap(~Vol, scales = "free_y")

ggplot(datos) +
  geom_point(aes(x = serie, y = abs(diferencia / Vol), color = clase, shape = as.factor(sign(diferencia)) )) +
  # Agregar target y error de 2%
  geom_hline(aes(yintercept = 1)) + geom_hline(aes(yintercept = 1+ 0.02), color="gray") + geom_hline(aes(yintercept = 1-0.02), color="gray") +
  # geom_hline(aes(yintercept = -1)) + geom_hline(aes(yintercept = -1 -0.02), color="gray") + geom_hline(aes(yintercept = -1 + 0.02), color="gray") +
  # ylim(c(-1.2,1.2)) +
  ggtitle("Pipeteo en paralelo pesando origen y destino",
          paste("rep4")) + 
  # paste("rep3: la serie 4 tiene 5% extra de loading, y se ve que en esa serie el source se separo del target hacia la zona de menos error.",
  # "Siempre cargó de menos, entonces es lógico que agregar 5% reduzca el error en source. Pero eso no eliminó el error en target; quizas no era falta de volumen.",
  # "El error relativo no es constante, indicando que el error en el diametro del embolo no es la unica fuente de error", sep = "\n")) + 
  theme_minimal() + facet_wrap(~Vol)

####### REP 5 ####

datos <- read.csv("data/21-07-05-p200-calib/calib_p200_4_0p5p.csv")
datos$diferencia <- (datos$peso_final - datos$peso_inicial)*1000
# datos$rownum <- 1:nrow(datos)

ggplot(datos) +
  geom_point(aes(x = serie, y = diferencia, color = clase )) +
  geom_hline(aes(yintercept = Vol)) +
  geom_hline(aes(yintercept = Vol+1), color="gray", alpha = .5, size=1.1) +
  geom_hline(aes(yintercept = Vol-1), color="gray", alpha = .5, size=1.1) +
  geom_hline(aes(yintercept = Vol+0.02*Vol), color="gray", linetype=2, alpha = .5, size=1.1) +
  geom_hline(aes(yintercept = Vol-0.02*Vol), color="gray", linetype=2, alpha = .5, size=1.1) +
  ggtitle("Pipeteo en paralelo pesando destino",
          paste("rep5: 0p es sin correccion al levantar, 5p es tomando 5% extra al levantar.", sep = "\n",
                "gris liso 1uL error, gris punteado 2% error.",
                "- Observé que siempre quedó volumen sin depositar en el tip, como era esperado.",
                "- Con el 5% extra hay una leve tendencia a depositar de menos a menor volumen, y viceversa.",
                "- En general se depositó más volumen al cargar 5% extra, aunque es menos marcado/seguro a volumen bajo."
          )) + 
  theme_minimal() + facet_wrap(~Vol, scales = "free_y")

# ggsave("results/21-07-05-p200-calib/rep4_0p_5p.png")

ggplot(datos) +
  geom_point(aes(x = serie, y = diferencia / Vol)) +
  # Agregar target y error de 2%
  geom_hline(aes(yintercept = 1)) +
  geom_hline(aes(yintercept = 1+ 0.02), color="gray") +
  geom_hline(aes(yintercept = 1-0.02), color="gray") +
  # geom_hline(aes(yintercept = -1)) + geom_hline(aes(yintercept = -1 -0.02), color="gray") + geom_hline(aes(yintercept = -1 + 0.02), color="gray") +
  # ylim(c(-1.2,1.2)) +
  ggtitle("Pipeteo en paralelo pesando origen y destino",
          paste("rep5: 0p es sin correccion al levantar, 5p es tomando 5% extra al levantar.")) + 
  theme_minimal() + facet_wrap(~Vol)
