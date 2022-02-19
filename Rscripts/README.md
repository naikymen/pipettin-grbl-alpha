# R code for pipettin-grbl

We use this version of R:

```
> R.version
               _
platform       arm-unknown-linux-gnueabihf
arch           arm
os             linux-gnueabihf
system         arm, linux-gnueabihf
status
major          3
minor          5.2
year           2018
month          12
day            20
svn rev        75870
language       R
version.string R version 3.5.2 (2018-12-20)
nickname       Eggshell Igloo
```

> R 3.5 is quite old, but this is what is packaged in `r-base` by our Ubuntu distribution for the raspberry pi.

## PCRmix protocol planner

### Requirements

* R 3.5.2
* Some packages: `install.packages(c("dendextend", "tidyr", "dplyr", "jsonlite"))`

### Code and usage

```sh
# First argument is the input JSON, and the second is the output JSON path
Rscript --vanilla ~/pipettin-grbl/Rscripts/pcr_planner.R ~/pipettin-grbl/Rscripts/sample_input.json ~/pipettin-grbl/Rscripts/sample_output2.json
```

See `pcr_planner.R`.

