#!/usr/bin/env Rscript

# Load libraries
library(jsonlite)
library(Cuentitas)
# devtools::load_all("~/Projects/Academia/Doctorado/gitlabs_acl/cuentitas-helper")

# Call example: Rscript --vanilla ~/pipettin-grbl/Rscripts/pcr_planner.R ~/pipettin-grbl/Rscripts/sample_input.json ~/pipettin-grbl/Rscripts/sample_output.json
args = commandArgs(trailingOnly=TRUE)
# json.input <- "~/Projects/Electronica/robot_pipeteador/pipettin-grbl/Rscripts/sample_input.json"
# json.input <- "~/Projects/Electronica/robot_pipeteador/pipettin-grbl/Rscripts/planerr_input.json"
json.input <- args[1]
# json.output <- "~/Projects/Electronica/robot_pipeteador/pipettin-grbl/Rscripts/sample_output.json"
json.output <- args[2]

# Get useful objects from input
protocol <- jsonlite::fromJSON(txt = json.input)
template <- protocol$templateDefinition
components <- protocol$templateDefinition$components

# Parse input
component_groups <- lapply(split(components, components$name), function(component){
  # component <- split(components, components$name)[[1]]  # for tests
  grupo <- list(
    template = component[["templates"]][[1]],
    pFw = component[["fwPrimers"]][[1]],
    pRv = component[["rvPrimers"]][[1]]
  )

  # for(i in seq_along(grupo)) if(length(grupo[[i]] < 2)) grupo[[i]] <- NULL
  return(grupo)
})

# Run PCRmix pipetting planner
stock_solutions_x = c(
    # pol = 100,                         # 100x (0.2 uL / 20 uL = 0.01)
    buffer = template$bufferStock,     # 10 x
    dNTPs = template$dntpsStock,       # 10 mM stock
    pFw = template$primerStock,        # uM
    pRv = template$primerStock         # uM
)
stock_solutions_vol = c(
    pol = 0.2,        # uL
    template = 1      # uL
)
target_solution = c(
    dNTPs = template$dntpsFinal,      # 0.1 mM final (10 mM is 100x). Recomiendan 50-200 uM, normalmente uso 0.2 final / 50 x.
    pFw = template$primerFinal,       # uM (50 x)
    pRv = template$primerFinal        # uM (50 x)
)
result <- Cuentitas::cuentitas5(
  component_groups = component_groups,
  extra_fraction = as.numeric(template$volLossCompensation),
  volume = as.numeric(template$finalVol),
  stock_solutions_x = stock_solutions_x,
  stock_solutions_vol = stock_solutions_vol,
  target_solution = target_solution,
  plot_dendrogram = F,
  cleanup = NULL
  # cleanup = "grupo"
  # cleanup = c("grupo", "total_vol", "mix_volume", "mix_x","n_reactions", "n_extra", "reaction_volume")
)

# Parse result and prepare recipes
recipes <- Cuentitas::make.recipe(result)

# Add component names
recipes$component_names = unique(c(names(stock_solutions_x), names(stock_solutions_vol)))

# Make PDF instructions
# recipe.pdf <- make.recipe.pdf(result = result,
#                               output.file = paste0(Sys.Date(), "-PCR.pdf")
#                               )

recurse.vectolist <- function(result){
  if(is.list(result)){
    for(i in seq_along(result)){
      result[[i]] <- recurse.vectolist(result[[i]])
    }
  } else {
    if(!is.null(names(result))) result <- as.list(result)
  }
  return(result)
}

# Write output
jsonlite::write_json(x = recurse.vectolist(recipes), path = json.output, pretty = F, auto_unbox=TRUE)
# json.output.content <- jsonlite::toJSON(x = recurse.vectolist(recipes), pretty = T)
