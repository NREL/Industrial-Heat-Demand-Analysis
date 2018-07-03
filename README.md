# Industrial-Heat-Demand-Analysis
This analysis characterizes the combustion energy demands of 14 significant industries in the U.S. It also includes calculation of facility-level annual energy demand from 2010 to 2015 based on greenhouse gas (GHG) emissions reported to the U.S. Environmental Protection Agency's Greenhouse Gas Reporting Program (GHGRP) (https://www.epa.gov/ghgreporting) and estimation of the potential to reduce fossil fuel use through three alternative heat generators (i.e., geothermal, solar industrial process heat [SIPH], and small modular nuclear reactors [SMRs]).
All code was written in Python 3.4.
## GHGRP Emissions Data
GHGRP emissions data for 2010 - 2015 are downloaded using the EPA Envirofacts API (https://www.epa.gov/enviro/envirofacts-data-service-api). After the required data are downloaded, combustion energy for the reporting facilities is estimated using the methodology described by McMillan et al. (2016) (https://doi.org/10.2172/1334495). Updated methodology includes expanded use of GHGRP-specified combustion unit types and data on combustion of wood and wood residuals in the pulp and paper industries (Subpart AA emissions). 
### /GHGRP_dl
This folder contains the methods for downloading GHGRP emissions data using EPA's API and for calculating the associated combustion energy. A known issue is incomplete data downloads using EPA's API. Includes data files for emission factors and identification of pulp and paper facilities reporting Subpart AA emissions.
### GHGRP_config.py
Code for downloading EPA GHGRP emissions data and calculating facility-level combustion energy. Calls the methods contained in Get_GHGRP_data.py, GHGRP_energy_calc.py, and GHGRP_AAenergy_calc.py.
#### Get_GHGRP_data.py
Methods for downloading the relevant GHGRP data from tables C_FUEL_LEVEL_INFORMATION, D_FUEL_LEVEL_INFORMATION, c_configuration_level_info, and V_GHG_EMITTER_FACILITIES via EPA RESTful API.
#### GHGRP_energy_calc.py
Methods for calculating facility-level combustion energy from GHGRP emissions data using the approach described by McMillan et al. (2016).
#### GHGRP_AAenergy_calc.py
Methods for formatting Subpart AA emissions data and calculating associated combustion energy.
## Target Industry Heat Characterization
Calculated combustion energy data for the 14 target industries is broken down by end use (e.g., process heating, cogeneration) using information provided by the GHGRP (when provided) and Energy Information Administration (EIA) Manufacturing Energy Consumption Survey (MECS) (https://www.eia.gov/consumption/manufacturing/). Energy by end use is further characterized by temperature range and load.
### Heat_CONFIG.py
The code for characterizing and analyzing target industry heat demand for 2010 - 2015. Calls the methods contined in Enduse_Calc.py, TargetInd_Format.py, SupSizing.py
#### Enduse_Calc.py
Methods for estimating energy use by end use (e.g., conventional boiler, process heating) based on GHGRP-reported unit types and unit names and using the Energy Information Administration (EIA) Manufacturing Energy Consumption Survey (2010, http://www.eia.gov/consumption/manufacturing/data/2010/). Also includes method for assigning temperature values by end use and industry.
#### TargetInd_Format.py
Methods for identifying and separating industries that are the focus of the analysis (target industries). Target industries were identified by McMillan et al. (2016).
#### SupSizing.py
Methods for matching target industries to alternative energy supplies, plotting load demand curves, and estimating savings associated with alternative energy supply matching.
### /data_for_heat_calcs
This folder contains assumptions and other supporting data used to characterize target industry heat demand.
### /notebooks
This folder contains Jupyter notebooks for data analysis and figure generation.
