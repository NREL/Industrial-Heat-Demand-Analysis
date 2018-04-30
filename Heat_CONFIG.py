# -*- coding: utf-8 -*-
"""
Created on Mon Sep 11 14:56:19 2017

@author: cmcmilla
"""

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import pysal as ps
import TargetInd_Format
import Enduse_Calc
import SupSizing
import MakeCountyMap

# This is the directory for files used in end-use calculations
filesdir = "U:\\Industrial Heat Survey\\Paper Version\\Data and analysis\\" + \
            "Data for calculations\\"

# This is the file location for relevant data downloaded from EPA's API
energy_file = "C:\\Users\\cmcmilla\\Desktop\\GHGRP_output\\" + \
            "GHGRP_all_20170908-1246.csv"

# This is total emissions, including biogenic
emissions_file = "GHGRP_emissions_201015.csv"

# This is only biogenic emissions
emissions_bio_file = "GHGRP_emissions_bio_201015.csv"

targetind_file = "target_industries.csv"

ihs_file = 'IHS_Process_info.xlsx'

efs_file = 'EPA_FuelEFs.csv'

eu_file = 'target_ind_enduses.csv'

ff_price_file = 'FF_prices.xlsx'

# MECS fuel types
MECS_fts = ['Coal', 'Diesel', 'LPG_NGL', 'Natural_gas', 'Other',
            'Residual_fuel_oil']

MECS_NAICS = pd.read_csv(filesdir + 'mecs_naics.csv')

fuelxwalkDict = dict(pd.read_csv(filesdir + 'MECS_FT_hs_wo-bio.csv')[[
        "EPA_FUEL_TYPE", "MECS_FT"]
        ].values
        )

bioxwalkDict = dict(pd.read_csv(filesdir + 'MECS_FT_hs_wo-bio.csv')[[
        "EPA_FUEL_TYPE", "Biogenic"]
        ].values
        )

target_energy = pd.read_csv(energy_file, index_col=0, encoding='latin1')

target_energy = TargetInd_Format.ti_format(
    energy_file, filesdir + targetind_file
    )

Enduse_Calc.MatchMECS_NAICS_FT(target_energy, 'FINAL_NAICS_CODE', MECS_NAICS,
                               fuelxwalkDict, bioxwalkDict
                               )

ihs_data = Enduse_Calc.import_IHS_data(filesdir + ihs_file)


target_ghgs = pd.read_csv(filesdir + emissions_file)

target_ghgs_bio = pd.read_csv(filesdir + emissions_bio_file)

target_ghgs_bio.rename(
    columns={'CO2E_EMISSION': 'CO2E_bio_GHGRP', 'YEAR': 'REPORTING_YEAR'},
    inplace=True
    )

target_ghgs.rename(
    columns={'CO2E_EMISSION': 'CO2E_GHGRP', 'YEAR': 'REPORTING_YEAR'},
    inplace=True
    )

target_ghgs = \
    pd.concat([
        target_ghgs.set_index(
            ['FACILITY_ID', 'REPORTING_YEAR', 'SUBPART_NAME']
            ), target_ghgs_bio.set_index(
            ['FACILITY_ID', 'REPORTING_YEAR', 'SUBPART_NAME']
            )
        ], axis=1)

target_ghgs.reset_index(drop=False, inplace=True)

target_ghgs = pd.DataFrame(
    target_ghgs[(target_ghgs.SUBPART_NAME == 'C') |
                (target_ghgs.SUBPART_NAME == 'D') |
                (target_ghgs.SUBPART_NAME == 'AA')
                ].groupby(
                    ['FACILITY_ID', 'REPORTING_YEAR']
                    )['CO2E_GHGRP', 'CO2E_bio_GHGRP'].sum(), copy=True
    )

target_ghgs.reset_index(inplace=True, drop=False)

#
# Create summary of bio and total GHG emissions for target industries
ID_NAICS = \
    dict(pd.DataFrame(
        target_energy[['FACILITY_ID', 'FINAL_NAICS_CODE']].reset_index(
            drop=True
            ).drop_duplicates(subset=['FACILITY_ID'])
            ).values
        )

for fid in ID_NAICS.keys():
    
    target_ghgs.loc[
        target_ghgs[target_ghgs.FACILITY_ID == fid].index, 'FINAL_NAICS_CODE'
        ] =\
        ID_NAICS[fid]
        
 # Drop non-target industry NAICS       
target_ghgs = target_ghgs[target_ghgs.FINAL_NAICS_CODE.notnull()]

target_ghg_summary = pd.DataFrame(target_ghgs, copy=True)

target_ghg_summary.loc[:, 'CO2E_fossil_GHGRP'] = \
    target_ghg_summary.CO2E_GHGRP.subtract(
        target_ghg_summary.CO2E_bio_GHGRP, fill_value=0
        )

# Convert to MMTCO2E
pivot_target_ghgs = pd.pivot_table(
    target_ghg_summary, index='FINAL_NAICS_CODE', columns='REPORTING_YEAR',
    values=['CO2E_bio_GHGRP', 'CO2E_fossil_GHGRP'], aggfunc='sum'
    ) /1000000
#
# %%
pivot_target_ghgs.to_csv('Target_GHGRP_GHG_summary.csv')
#

# %%
# Calculate energy by end use. Eu_results is a dictionary of dataframes:
# 'target_enduse' is calculated end use energy based on MECS data and
# GHGRP unit type designations and 'eu_noMECS' is end use energy calcualted
# using only GHGRP unit type designations.
eu_results = \
    Enduse_Calc.enduse_calc(target_energy, ihs_data, filesdir + eu_file)

# Check portion of total calculated energy by MECS fuel type is captured by
# end use calculations. Need to first separate individual end uses from the 
# aggregate categories.
MECS_enduses_all = list(eu_results['target_enduse'].END_USE.drop_duplicates())

eu_list = []

for i in [1, 2, 4, 5, 6, 7, 8, 9]:
    eu_list.append(MECS_enduses_all[i])

eu_results['target_enduse'].loc[:, 'for_EU_sum'] = \
    eu_results['target_enduse'].END_USE.apply(lambda x: x in eu_list)

#
# This is the output of portion of total calculated energy that is 
# captured bye end use calculations (doesn't break out by year).
eu_results['target_enduse'][
    eu_results['target_enduse'].for_EU_sum == True][MECS_fts].sum() / \
    target_energy.groupby('MECS_FT').TJ.sum()

# %%
# For related energy values (doesn't break out by year):
(1 - eu_results['target_enduse'][
    eu_results['target_enduse'].for_EU_sum == True][MECS_fts].sum() / \
    target_energy.groupby('MECS_FT').TJ.sum()) * \
    target_energy.groupby('MECS_FT').TJ.sum() / target_energy.TJ.sum()

# for LPG-NGL:
22283.899 /  target_energy.TJ.sum()

# To break out by year:
(1- eu_results['target_enduse'][
    eu_results['target_enduse'].for_EU_sum == True
    ].groupby('REPORTING_YEAR')[MECS_fts].sum().divide(
        pd.pivot_table(target_energy, index='REPORTING_YEAR',
                       columns='MECS_FT', values='TJ', aggfunc='sum')
                       )) * \
    pd.pivot_table(
        target_energy, index='REPORTING_YEAR',columns='MECS_FT', values='TJ',
        aggfunc='sum').divide(
               target_energy.groupby('REPORTING_YEAR').TJ.sum(), axis=0
               )
# %%
# Create mapping of heat characteristics.
target_char = Enduse_Calc.heat_mapping(
    eu_results['target_enduse'], ihs_data, proc_char='temp'
    )

# Calculate ghg emissions by heat characteristic.
target_char = Enduse_Calc.ghg_calc(
    filesdir + efs_file, target_char, fuelxwalkDict, bioxwalkDict
    )

# Output file for use in jupyter notebook
target_char.to_csv(
    "C:\\Users\\cmcmilla\\Desktop\\GHGRP_output\\target_char.csv"
    )

##
# Calulate matched load and matched supply for each facility
# Also draws and saves load and energy curves for 2010 - 2015
alt_load, all_load, supply_match = SupSizing.AltES_Sizing(target_char, True)

##
# Plot figure for facility load and temperature, along with alt gen
# for a given year
SupSizing.DrawMatchPlot(supply_match, all_load, 2015)

#%%
# Calculate annual fossil fuel and GHG savings by alt gen
supply_savings, target_char = \
    SupSizing.MatchedSavings(supply_match, target_char)

xlswriter = pd.ExcelWriter('Savings_by_supply.xls')
for df in supply_savings.keys():
    supply_savings[df].to_excel(xlswriter, sheet_name=df)

xlswriter.save()
#
# %%
# Summarize annual fossil fuel use by temperature range
pd.pivot_table(
    target_char[target_char.Biogenic == False], 
    index=['REPORTING_YEAR', 'Temp_Band'],values=MECS_fts, aggfunc=np.sum
    ).to_csv('Baseline_ff_use_IPH_temprange.csv')

# Calculate annual GHG savings of alternative heat supplies. 
ghg_savings, ff_savings = Enduse_Calc.alt_heat_savings(
    target_ghgs, target_char, target_energy
    )

ghg_savings.loc[:, 'CO2E_fossil_GHGRP'] = \
    ghg_savings.CO2E_GHGRP.subtract(ghg_savings.CO2E_bio_GHGRP, fill_value=0)

#
# Create summary table of annual GHG savings and ff savings by industry
ghg_savings_summ = pd.DataFrame(
    ghg_savings.groupby(
        ['FINAL_NAICS_CODE', 'REPORTING_YEAR']
        )[['savings_MMTCO2E_total', 'savings_MMTCO2E_bio']].sum()
    )

ff_savings_summ = pd.DataFrame(
    ff_savings.drop(['Savings_percent', 'FACILITY_ID'], axis=1).groupby(
        ['FINAL_NAICS_CODE', 'REPORTING_YEAR']
        ).sum()
        )
        
ff_savings_summ.loc[:, 'Savings %'] = \
    ff_savings_summ.Savings_Total.divide(
        ff_savings_summ.Original_Total, fill_value=0)

ghg_savings_summ.loc[:, 'Savings (fossil only) MMTCO2E'] = \
    ghg_savings_summ.savings_MMTCO2E_total.subtract(
        ghg_savings_summ.savings_MMTCO2E_bio, fill_value=0
        )

ghg_savings_summ.loc[:, 'Savings %'] = \
    ghg_savings_summ['savings_MMTCO2E_total'].divide(
        ghg_savings.groupby(
            ['FINAL_NAICS_CODE', 'REPORTING_YEAR']
            ).CO2E_GHGRP.sum(), fill_value=0
        )

ghg_savings_summ.loc[:, 'Savings (fossil only) %'] = \
    ghg_savings_summ['Savings (fossil only) MMTCO2E'].divide(
        ghg_savings.groupby(
            ['FINAL_NAICS_CODE', 'REPORTING_YEAR']
            ).CO2E_fossil_GHGRP.sum(), fill_value=0
        )

ghg_savings_summ.drop(['savings_MMTCO2E_bio'], inplace=True, axis=1)

ghg_savings_summ.rename(
    columns={'savings_MMTCO2E_total': 'Savings MMTCO2E'}, inplace=True
    )

# Annual total savings
ghg_savings_summ.sum(level='REPORTING_YEAR')['Savings MMTCO2E'].divide(
    pd.pivot_table(
        ghg_savings, index='FINAL_NAICS_CODE', columns='REPORTING_YEAR',
        values='CO2E_GHGRP', aggfunc=np.sum
        ).sum(axis=0)
    )
#
#
# Calculate annual dollar values of fossil fuel savings (in $B)
ff_prices = pd.read_excel(
    filesdir + ff_price_file, sheetname='Dollar_per_TJ',
    index_col='REPORTING_YEAR'
    )    

ff_dollar_savings = pd.pivot_table(
    ff_savings_summ.reset_index(drop=False), index='REPORTING_YEAR',
    values=['Coal', 'Diesel', 'LPG_NGL', 'Natural_gas', 'Residual_fuel_oil'],
    aggfunc=np.sum
    )
    
ff_dollar_savings = ff_prices.multiply(ff_dollar_savings)/1000000000

ff_dollar_savings.loc[:, 'Total'] = ff_dollar_savings.sum(axis=1)

# National energy expenditures in $B
total_exp = \
    np.array([1213.336, 1392.945, 1356.215, 1378.885, 1399.486, 1127.132])
    
ff_dollar_savings.loc[:, 'Fraction_US_Exp'] = \
    ff_dollar_savings.Total.divide(total_exp)*100

ff_dollar_savings.apply(lambda x: np.round(x, decimals=3)).to_csv(
    'FF_dollar_savings_summary.csv'
    )

# GHG emissions summary by year, NAICS, and temperature
target_char.groupby(
    ['REPORTING_YEAR', 'Temp_degC', 'FINAL_NAICS_CODE']
    ).MMTCO2E.sum()

# 
#pd.concat([pd.concat([pd.concat(
#    [ff_savings_summ.xs(2015, level='REPORTING_YEAR')['Savings_Total']/1000,
#     ghg_savings_summ.xs(2015, level='REPORTING_YEAR')['Savings MMTCO2E']],
#    axis=1), pd.pivot_table(ghg_savings[ghg_savings.REPORTING_YEAR==2015],
#    values='CO2E_GHGRP', aggfunc=np.sum, index='FINAL_NAICS_CODE')], axis=1
#    ), target_energy[(target_energy.REPORTING_YEAR == 2015) & 
#        (target_energy.Biogenic == False)].groupby('TJ').sum())/1000], axis=1).sort_values(
#            'Savings_Total', ascending=False
#            )
 

# %%
# Create county map of average annual total GHG savings
# First create mapping dataset

savings_map_data = \
    pd.DataFrame(
        ghg_savings[ghg_savings.savings_MMTCO2E_total.notnull()], copy=True
        )

ID_FIPS_dict = dict(
    target_energy.reset_index(drop=True).drop_duplicates('FACILITY_ID')[
        ['FACILITY_ID', 'COUNTY_FIPS']
        ].values
    )

savings_map_data.loc[:, 'COUNTY_FIPS'] = savings_map_data.FACILITY_ID.apply(
    lambda x: ID_FIPS_dict[x]
    )
 
savings_map_data = savings_map_data[savings_map_data.COUNTY_FIPS !=0] 

savings_map_data.dropna(subset=['savings_MMTCO2E_total'], axis=0, inplace=True)

# %%
for y in [2015]:

#    savings_map_data = pd.DataFrame(
#        savings_map_data[savings_map_data.REPORTING_YEAR == y].groupby(
#            ['COUNTY_FIPS', 'FACILITY_ID'], as_index=False
#            ).savings_MMTCO2E_total_mean.mean()
#            )

    savings_map_data_input = pd.DataFrame(
        savings_map_data[savings_map_data.REPORTING_YEAR == y].groupby(
            'COUNTY_FIPS', as_index=False
            ).savings_MMTCO2E_total.sum()
        )
        
#    FJ_2011 = ps.Fisher_Jenks(
#        savings_map_data_input.savings_MMTCO2E_total, k = 5
#        )

    savings_map = MakeCountyMap.CountyEnergy_Maps(savings_map_data_input)
    
    if y == 2015:
        
        savings_map.make_map('savings_MMTCO2E_total', 5, FJ_2011)
    
    else:
        
        savings_map.make_map('savings_MMTCO2E_total', 5)

    print(np.round(
        ps.Fisher_Jenks(savings_map_data_input.savings_MMTCO2E_total, k = 5).bins,
        decimals=1)
        )
        