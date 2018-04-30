# Industrial-Heat-Demand-Analysis
This analysis characterizes the combustion energy demands of 14 significant industries in the U.S. It also includes calculation of facility-level annual energy demand from 2010 to 2015 based on greenhouse gas (GHG) emissions reported to the U.S. Environmental Protection Agency's Greenhouse Gas Reporting Program (GHGRP) (https://www.epa.gov/ghgreporting) and estimation of the potential to reduce fossil fuel use through three alternative heat generators (i.e., geothermal, solar industrial process heat [SIPH], and small modular nuclear reactors [SMRs]).
## GHGRP Emissions Data
GHGRP emissions data for 2010 - 2015 are downloaded using the EPA Envirofacts API (https://www.epa.gov/enviro/envirofacts-data-service-api). After the required data are downloaded, combustion energy for the reporting facilities is estimated using the methodology described by McMillan et al. (2016) (https://doi.org/10.2172/1334495). 
### /GHGRP_dl
This folder contains the code for downloading GHGRP emissions data and for calculating the associated combustion energy.
## Target Industry Heat Characterization
Calculated combustion energy data for the 14 target industries is broken down by end use (e.g., process heating, cogeneration) using information provided by the GHGRP (when provided) and Energy Information Administration (EIA) Manufacturing Energy Consumption Survey (MECS) (https://www.eia.gov/consumption/manufacturing/). Energy by end use is further characterized by temperature range and load.
### /data_for_heat_calcs
This folder contains assumptions and other supporting data used to characterize target industry heat demand.
### Heat_CONFIG.py
The code for characterizing and analyzing target industry heat demand for 2010 - 2015.
## /notebooks
This folder contains Jupyter notebooks for data analysis and figure generation.
