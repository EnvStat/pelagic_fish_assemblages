This repository presents the code for the manuscript

Community-level modelling of pelagic fish assemblages in the Baltic Sea reveals temporal shifts and effects of environmental drivers

Manuscript DOI:  https://doi.org/10.1093/icesjms/fsag166

Links for the larger data files:
https://doi.org/10.5281/zenodo.22027768

Links for the larger results files:
https://doi.org/10.5281/zenodo.22014190



The algorithm consists of the following steps:

1) Running scripts starting with 1 would aggregate data for the analysis.
Alternatively, one can upload the data files from https://doi.org/10.5281/zenodo.22027768

2) Run main.py, which runs MCMC analysing the data

3) Run files starting with 2_ for the analysis.

4) Run files starting with 3_ for some extra analysis.


Some other scripts are used for supportive functions / visualisation


dependencies:
* python 3.10.12
* numpy 1.26.4
* scipy 1.15.3
* pandas 2.3.0
* PIL 9.0.1
* geopy 2.2.0
