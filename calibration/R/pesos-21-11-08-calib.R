####### REP 1 ####

results_dir <- "results/21-11-08-p200-calib/"
results_file <- "data/21-11-08-p200/serie_x4_triplicado-reciprocal_correction.ods"

datos <- readODS::read_ods(results_file)
datos$diferencia <- datos$Pesado
datos$Vol <- datos$Esperado
# datos$rownum <- 1:nrow(datos)

datos$error <- datos$Esperado - datos$Pesado

library(ggplot2)

# datos <- dplyr::filter(datos, correction == "backslash+linear")

ggplot(datos) +
  geom_line(aes(x = Orden, 
                y = Pesado, 
                color = as.factor(retract_backpour),
                group = as.factor(Serie)
  )) +
  geom_hline(aes(yintercept = Vol)) +
  geom_hline(aes(yintercept = Vol-1), color = "gray", linetype = 2) +
  geom_hline(aes(yintercept = Vol+1), color = "gray", linetype = 2) +
  
  facet_wrap(~correction, scales = "free") + 
  
  ggtitle("Masas del pipeteo en serie", "Targets en lineas horizontales +/-1 uL") + theme_minimal()

dir.create(results_dir)
ggsave(paste0(results_dir,"/","pruebas_serie.png"))

####

datos_lin <- dplyr::filter(datos, correction == "backslash+linear")

ggplot(datos_lin) +
  geom_line(aes(x = Orden, 
                y = Pesado, 
                color = interaction(s_retract_parameter, back_pour_param, sep = "_"),
                group = as.factor(Serie)
  )) +
  geom_hline(aes(yintercept = Vol)) +
  geom_hline(aes(yintercept = Vol-1), color = "gray", linetype = 2) +
  geom_hline(aes(yintercept = Vol+1), color = "gray", linetype = 2) +
  
  facet_wrap(~correction, scales = "free") + 
  
  ggtitle("Masas del pipeteo en serie", "Targets en lineas horizontales +/-1 uL") + theme_minimal()

dir.create(results_dir)
ggsave(paste0(results_dir,"/","pruebas_serie.png"))


ggplot(datos_lin) +
  geom_boxplot(aes(x = Orden, 
                   y = Pesado,
                   group=Orden)) +
  geom_hline(aes(yintercept = Vol)) +
  geom_hline(aes(yintercept = Vol-1), color = "gray", linetype = 2) +
  geom_hline(aes(yintercept = Vol+1), color = "gray", linetype = 2) +
  
  facet_wrap(~correction, scales = "free") + 
  
  ggtitle("Masas del pipeteo en serie", "Targets en lineas horizontales +/-1 uL") + theme_minimal()

dir.create(results_dir)
ggsave(paste0(results_dir,"/","pruebas_serie_bxplt.png"))

# Conseve de la ultima prueba:
# Bajar el backslash compensation a 0.1 de 0.5
# Hacer que tome de más al inicio (como ya hace) pero que luego largue un poquito (1 uL). 
# Hacer una correccion lineal (ver "efecto_capilaridad.rmd") a volumenes bajos.

# Resultado
# Logré que el último punto no sea tan horroroso.
# Todavía no corregí el problema del "over dispensing" en los primeros (3) puntos.
#   Honestamente ni idea por qué pasa eso, pero el efecto es re consistente.
#   Al mismo tiempo, está dentro del error feo de la balanza analítica, así que ya fue por ahora.

ggplot(datos_lin) +
  geom_boxplot(aes(x = Orden, 
                   y = Pesado/Esperado,
                   group=Orden)) +
  geom_hline(aes(yintercept = 1)) +
  geom_hline(aes(yintercept = 1-0.01), color = "gray", linetype = 2) +
  geom_hline(aes(yintercept = 1+0.01), color = "gray", linetype = 2) +
  
  facet_wrap(~correction, scales = "free") + 
  
  ggtitle("Masas del pipeteo en serie", "Error del 1% en líneas horizontales") + theme_minimal()

dir.create(results_dir)
ggsave(paste0(results_dir,"/","pruebas_serie_bxplt_rel.png"))
