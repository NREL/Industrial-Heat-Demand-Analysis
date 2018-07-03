# -*- coding: utf-8 -*-
"""
Created on Thu Jul 27 14:04:47 2017
@Colin McMillan, colin.mcmillan@nrel.gov
"""

import pandas as pd

import numpy as np

import requests

import json
#
#
# Import EPA GHG emission factors for fuel types.
# Most emission factors originated from GHGRP guidance; additional values
# have been added for "Biogas (Captured methane)", "Coke" (assumed to be
# from coal), and "Wood and Wood Residuals" based on
# EPA 2014 emission factors from http://www.epa.gov/sites/production/files/
# 2015-12/documents/emission-factors_nov_2015.pdf
#
#EFs = pd.read_csv('EPA_FuelEFs.csv', index_col = ['Fuel_Type'])
#
#EFs['dup_index'] = EFs.index.duplicated()
#
#EFs = pd.DataFrame(EFs[EFs.dup_index == False], columns = EFs.columns[0:2])


def fipfind(f, missingfips):

    z2f = json.load(open('zip2fips.json'))

    if np.isnan(missingfips.loc[f, 'LATITUDE']) == False:

        lat = missingfips.loc[f, 'LATITUDE']

        lon = missingfips.loc[f, 'LONGITUDE']

        payload = {
            'format': 'json', 'latitude': lat, 'longitude': lon,
            'showall': 'true'
            }

        r = requests.get('http://data.fcc.gov/api/block/find?', 
            params=payload
            )

        fipfoud = r.json()['County']['FIPS']

        return fipfoud

    if ((missingfips.loc[f, 'ZIP'] > 1000) 

        & (np.isnan(missingfips.loc[ f, 'COUNTY_FIPS'])==True) 

        & (str(missingfips.loc[f, 'ZIP']) in z2f)):

        fipfound = int(z2f[str(missingfips.loc[f,'ZIP'])])

        return fipfound

    else:

        fipfound = 0

        return fipfound

def format_GHGRP_emissions(c_fuel_file, d_fuel_file):
    """
    Import csv files for C_FUEL_LEVEL_INFORMATION and D_FUEL_LEVEL_INFORMATION
    for a given year. Format and correct for odd issues with reported data.
    """
    c_ghgs = pd.read_csv(
        c_fuel_file, encoding='latin_1', low_memory=False, index_col=0
        )

    d_ghgs = pd.read_csv(
        d_fuel_file, encoding='latin_1', index_col=0, low_memory=False
        )

#    c_ghgs = c_fuel_file
#
#    d_ghgs = d_fuel_file

    GHGs = pd.concat([c_ghgs, d_ghgs], axis=0, ignore_index=True)

    GHGs.dropna(axis=0, subset=['FACILITY_ID'], inplace=True)

#    if True in [type(x) == np.str for x in GHGs.REPORTING_YEAR.values]:
#
#        GHGs = \
#            GHGs[
#                GHGs.REPORTING_YEAR.apply(lambda x: type(x) == np.int) == True
#                ]

    for c in ('FACILITY_ID', 'REPORTING_YEAR'):

        GHGs.loc[:, c] = [int(x) for x in GHGs[c]]

    #Adjust multiple reporting of fuel types
    fuel_fix_index = GHGs[(GHGs.FUEL_TYPE.notnull() == True) & 
        (GHGs.FUEL_TYPE_OTHER.notnull() == True)].index

    GHGs.loc[fuel_fix_index, 'FUEL_TYPE_OTHER'] = np.nan

    # Fix errors in reported data.
    if GHGs.REPORTING_YEAR.drop_duplicates().values[0] == 2014:
        
        for i in list(GHGs[(GHGs.FACILITY_ID == 1005675) & \
            (GHGs.REPORTING_YEAR == 2014)].index):

            GHGs.loc[i, 'TIER2_CH4_EMISSIONS_CO2E'] = \
                GHGs.loc[i, 'TIER2_CH4_COMBUSTION_EMISSIONS'] * 25.135135

            GHGs.loc[i, 'TIER2_N2O_EMISSIONS_CO2E'] = \
                GHGs.loc[i, 'TIER2_N2O_COMBUSTION_EMISSIONS'] * 300

        for i in GHGs[(GHGs.FACILITY_ID == 1001143) & \
            (GHGs.REPORTING_YEAR == 2014)].index:
    
    	        GHGs.loc[i, 'T4CH4COMBUSTIONEMISSIONS'] = \
                GHGs.loc[i, 'T4CH4COMBUSTIONEMISSIONS']/1000
    
    	        GHGs.loc[i, 'T4N2OCOMBUSTIONEMISSIONS'] = \
                GHGs.loc[i, 'T4N2OCOMBUSTIONEMISSIONS']/1000
    
    if GHGs.REPORTING_YEAR.drop_duplicates().values[0] == 2012:
        
        selection = GHGs.loc[
            (GHGs.FACILITY_ID == 1000415) & (GHGs.FUEL_TYPE == 'Bituminous')
            ].index
            
        GHGs.loc[selection, 
                 ('T4CH4COMBUSTIONEMISSIONS'):('TIER4_N2O_EMISSIONS_CO2E')
                 ] = GHGs.loc[selection, 
                     ('T4CH4COMBUSTIONEMISSIONS'):('TIER4_N2O_EMISSIONS_CO2E')
                     ] / 10
            

    GHGs.loc[:, 'CO2e_TOTAL'] = 0
    
    total_co2 = pd.DataFrame()
 
    for tier in ['TIER1_', 'TIER2_', 'TIER3_']:

        for ghg in ['CH4_EMISSIONS_CO2E', 'N2O_EMISSIONS_CO2E', \
            'CO2_COMBUSTION_EMISSIONS']:
            
            total_co2 = pd.concat([total_co2, GHGs[tier + ghg]], axis=1)

#            GHGs.loc[:, 'CO2e_TOTAL'] = \
#                GHGs['CO2e_TOTAL'] + GHGs[tier + '_' + ghg].fillna(0)

    for ghg in ['TIER4_CH4_EMISSIONS_CO2E', 'TIER4_N2O_EMISSIONS_CO2E']:

        total_co2 = pd.concat([total_co2, GHGs[ghg]], axis=1)
        
    total_co2.fillna(0, inplace=True)
    
    GHGs.loc[:, 'CO2e_TOTAL'] = total_co2.sum(axis=1)
#       

#       GHGs.loc[:, 'CO2e_TOTAL'] = GHGs.loc[:, 'CO2e_TOTAL'] + \
#            GHGs[ghg].fillna(0)

#    Identify non-standard fuel types
#    allfuels = pd.concat(
#
#    	[GHGs['FUEL_TYPE_BLEND'], GHGs['FUEL_TYPE'], GHGs['FUEL_TYPE_OTHER']]
#
#    	).drop_duplicates()
#
#    allfuels = pd.DataFrame(allfuels.values, columns = ['FUEL_TYPE'])
#    allfuels['EF?'] = [i in EFs.index for i in allfuels['FUEL_TYPE'].values]
#    customfuels = allfuels.FUEL_TYPE[allfuels['EF?'] == False]
#    customfuels.to_csv('CustomFuelsforEF.csv')
#
#    Calculate fraction of GHG emissions from non-standard fuel types
#    This calculation does not match total CO2e reported in EPA's FLIGHT due to
#    different treatment of biogenic emission sources. Also does not include
#    CO2 emissions calculated using Tier 4 methodology.
#    GHGs['STRD_FUEL'] = [f in EFs.index for f in GHGs['FUEL_TYPE'].values]
#
#    cust_fraction_2014 = 1 - GHGs.CO2e_TOTAL[(GHGs['REPORTING_YEAR'] == 2014)
#
#    	& (GHGs['STRD_FUEL'] == True) ].sum()/ GHGs.CO2e_TOTAL[GHGs[
#
#    		'REPORTING_YEAR'] == 2014].sum()
#    This fraction is small (<1%); assume that calculating energy values of
#    non-standard fuel types can be omitted

    return GHGs


def format_GHGRP_facilities(fac_file_2010, oth_facfiles):

    """
    Format csv file of facility information. Requires list of facility
    files for 2010 and for subsequent years.
    Assumes 2010 file has the correct NAICS code for each facilitiy;
    subsequent years default to the code of the first year a facility
    reports.
    """

    MECS_regions = \
        pd.read_csv('US_FIPS_Codes.csv', index_col=['COUNTY_FIPS'])

    def fac_read_fix(ffile):
        """
        Reads and formats facility csv file.
        """
        facdata = pd.read_csv(ffile, encoding='latin_1', index_col=0)

#        Duplicate entries in facility data query. Remove them to enable a 1:1
#        mapping of facility info with ghg data via FACILITY_ID.
#        First ID facilities that have cogen units.
        fac_cogen = facdata.FACILITY_ID[
            facdata['COGENERATION_UNIT_EMISS_IND'] == 'Y'
            ]

#        facdata.drop_duplicates('FACILITY_ID', inplace=True)

        facdata.dropna(subset=['FACILITY_ID'], inplace=True)

#        Reindex dataframe based on facility ID
        facdata.FACILITY_ID = facdata.FACILITY_ID.apply(np.int)

#        Correct PRIMARY_NAICS_CODE from 561210 to 324110 for Sunoco Toledo 
#        Refinery (FACILITY_ID == 1001056); correct PRIMARY_NAICS_CODE from 
#        331111 to 324199 for Mountain State Carbon, etc.
        fix_dict = {1001056: {'PRIMARY_NAICS_CODE': 324110},
                1001563: {'PRIMARY_NAICS_CODE': 324119},
                1006761: {'PRIMARY_NAICS_CODE': 331221},
                1001870: {'PRIMARY_NAICS_CODE': 325110},
                1006907: {'PRIMARY_NAICS_CODE': 424710},
                1006585: {'PRIMARY_NAICS_CODE': 324199},
                1002342: {'PRIMARY_NAICS_CODE': 325222},
                1002854: {'PRIMARY_NAICS_CODE': 322121},
                1007512: {'SECONDARY_NAICS_CODE': 325199},
                1004492: {'PRIMARY_NAICS_CODE': 541712},
                1002434: {'PRIMARY_NAICS_CODE': 322121,
                'SECONDARY_NAICS_CODE': 322222},
                1002440: {'SECONDARY_NAICS_CODE': 221210},
                1002440: {'PRIMARY_NAICS_CODE': 325311},
                1003006: {'PRIMARY_NAICS_CODE': 324110},
                }

        for k, v in fix_dict.items():
            facdata.loc[facdata[facdata.FACILITY_ID == k].index, 
                        list(v)[0]] = list(v.values())[0]

        facdata.set_index(['FACILITY_ID'], inplace=True)

#        Re-label facilities with cogen units
        facdata.loc[fac_cogen, 'COGENERATION_UNIT_EMISS_IND'] = 'Y'

        facdata['MECS_Region'] = ""

        return facdata

    all_fac = fac_read_fix(fac_file_2010)

    for f in oth_facfiles:

        ff_y = fac_read_fix(f)

        all_fac = all_fac.append(ff_y)

#    Drop duplicated facility IDs, keeping first instance (i.e., year).
    all_fac = pd.DataFrame(all_fac[~all_fac.index.duplicated(keep='first')])

#    Identify facilities with missing County FIPS data and fill missing data.
#    Most of these facilities are mines or natural gas/crude oil processing
#    plants.

    ff_index = all_fac[all_fac.COUNTY_FIPS.isnull() == False].index

    all_fac.loc[ff_index, 'COUNTY_FIPS'] = \
        [np.int(x) for x in all_fac.loc[ff_index, 'COUNTY_FIPS']]

#    Update facility information with new county FIPS data
    missingfips = pd.DataFrame(all_fac[all_fac.COUNTY_FIPS.isnull() == True])

    missingfips.loc[:, 'COUNTY_FIPS'] = \
        [fipfind(i, missingfips) for i in missingfips.index]

    all_fac.loc[missingfips.index, 'COUNTY_FIPS'] = missingfips.COUNTY_FIPS

    all_fac['COUNTY_FIPS'].fillna(0, inplace=True)


#    Assign MECS regions and NAICS codes to facilities and merge location data
#    with GHGs dataframe.
#    EPA data for some facilities are missing county fips info
    all_fac.COUNTY_FIPS = all_fac.COUNTY_FIPS.apply(np.int)

    concat_mecs_region = \
        pd.concat(
            [all_fac.MECS_Region, MECS_regions.MECS_Region], axis=1, \
                join_axes=[all_fac.COUNTY_FIPS]
            )

    all_fac.loc[:,'MECS_Region'] = concat_mecs_region.iloc[:, 1].values

    all_fac.rename(columns = {'YEAR': 'FIRST_YEAR_REPORTED'}, inplace=True)
    
    all_fac.reset_index(drop=False, inplace=True)

    return all_fac


def MMBTU_calc_CO2(GHGs, c, EFs):
    """
    Calculate MMBtu value based on reported CO2 emissions.
    Does not capture emissions and energy from facilities using Tier 4
    calculation methodology.
    """
    emissions = GHGs[c].fillna(0)*1000

    name = GHGs[c].name[0:5]+'_MMBtu'

    df_energy = pd.DataFrame()

    for fuel_column in ['FUEL_TYPE', 'FUEL_TYPE_OTHER', 'FUEL_TYPE_BLEND']:

        fuel_index = GHGs.loc[emissions.index, fuel_column].dropna().index

        mmbtu = emissions.loc[fuel_index] / \
            GHGs.loc[fuel_index, fuel_column].map(EFs['CO2_kgCO2_per_mmBtu'])

        df_energy = pd.concat([df_energy, mmbtu], axis=0)

    df_energy.columns = [name]

    df_energy.sort_index(inplace=True)

    return df_energy


def MMBTU_calc_CH4(GHGs, c, EFs):
    """
    Calculate MMBtu value based on CH4 emissions reported under Tier 4.
    """
    emissions = GHGs[c].fillna(0) * 1000000

    name = GHGs[c].name[0:5] + '_MMBtu'

    df_energy = pd.DataFrame()

    for fuel_columns in ['FUEL_TYPE', 'FUEL_TYPE_OTHER', 'FUEL_TYPE_BLEND']:

        fuel_index = GHGs.loc[emissions.index, fuel_columns].dropna().index

        mmbtu = emissions.loc[fuel_index] / \
            GHGs.loc[fuel_index, fuel_columns].map(EFs['CH4_gCH4_per_mmBtu'])

        df_energy = pd.concat([df_energy, mmbtu], axis=0)

    df_energy.columns = [name]

    df_energy.sort_index(inplace=True)

    return df_energy

def calculate_energy(GHGs, all_fac, EFs, wood_facID):
    """
    Apply MMBTU_calc_CO2 function to EPA emissions table Tier 1, Tier 2, and
    Tier 3 emissions; MMBTU_calc_CH4 for to Tier 4 CH4 emissions.
    Adds heat content of fuels reported under 40 CFR Part 75 (electricity
    generating units and other combustion sources covered under EPA's
    Acid Rain Program).
    """
    merge_cols = list(all_fac.columns.difference(GHGs.columns))

    merge_cols.append('FACILITY_ID')

    GHGs = pd.merge(
        GHGs, all_fac[merge_cols], how='inner', on='FACILITY_ID'
        )

#   First, zero out 40 CFR Part 75 energy use for electric utilities
    GHGs.loc[GHGs[GHGs.PRIMARY_NAICS_CODE == 221112].index,
        'TOTAL_ANNUAL_HEAT_INPUT'] = 0

    GHGs.loc[GHGs[GHGs.PRIMARY_NAICS_CODE == 221112].index,
        'PART_75_ANNUAL_HEAT_INPUT'] = 0

    # Correct for revision in 2013to Table AA-1 emission factors for kraft 
    # pulping liquor emissions. CH4 changed from 7.2g CH4/MMBtu HHV to 
    # 1.9g CH4/MMBtu HHV.
    if GHGs.REPORTING_YEAR[0] in [2010, 2011, 2012]:
       
        GHGs.loc[:, 'wood_correction'] = [
            x in wood_facID.index for x in GHGs.FACILITY_ID
            ] and [f == 'Wood and Wood Residuals' for f in GHGs.FUEL_TYPE]

        GHGs.loc[(GHGs.wood_correction == True), 'T4CH4COMBUSTIONEMISSIONS'] =\
            GHGs.loc[
                (GHGs.wood_correction == True), 'T4CH4COMBUSTIONEMISSIONS'
                ].multiply(1.9 / 7.2)    

    # Separate, additional correction for facilities appearing to have 
    # continued reporting with previous CH4 emission factor for kraft liquor
    #combusion (now reported as Wood and Wood Residuals (dry basis).
    if GHGs.REPORTING_YEAR[0] == 2013:

        wood_fac_add = [1001892, 1005123, 1006366, 1004396]

        GHGs.loc[:, 'wood_correction_add'] = \
                [x in wood_fac_add for x in GHGs.FACILITY_ID]

        GHGs.loc[(GHGs.wood_correction_add == True) & 
            (GHGs.FUEL_TYPE == 'Wood and Wood Residuals (dry basis)'), 
                'T4CH4COMBUSTIONEMISSIONS'] =\
                GHGs.loc[(GHGs.wood_correction_add == True) & 
                    (GHGs.FUEL_TYPE == 'Wood and Wood Residuals (dry basis)'), 
                        'T4CH4COMBUSTIONEMISSIONS'].multiply(1.9 / 7.2)    

    co2columns = \
        ['TIER1_CO2_COMBUSTION_EMISSIONS', 'TIER2_CO2_COMBUSTION_EMISSIONS',
        'TIER3_CO2_COMBUSTION_EMISSIONS']

    df_mmbtu_CO2 = pd.concat(
        [MMBTU_calc_CO2(GHGs, c, EFs) for c in co2columns],  axis=1
        )

    df_mmbtu_CH4 = \
        pd.DataFrame(MMBTU_calc_CH4(GHGs, 'T4CH4COMBUSTIONEMISSIONS', EFs))

    df_mmbtu_all = pd.concat([df_mmbtu_CO2, df_mmbtu_CH4], axis=1)

    df_mmbtu_all.fillna(0, inplace=True)

    df_mmbtu_all.loc[:, 'TOTAL'] = df_mmbtu_all.sum(axis=1)

    GHGs.PART_75_ANNUAL_HEAT_INPUT.fillna(0, inplace=True)

    GHGs.loc[:, 'MMBtu_TOTAL'] = 0

    GHGs.MMBtu_TOTAL = df_mmbtu_all.TOTAL

    GHGs.loc[:, 'MMBtu_TOTAL'] = \
        GHGs[['MMBtu_TOTAL', 'PART_75_ANNUAL_HEAT_INPUT',
        'TOTAL_ANNUAL_HEAT_INPUT']].sum(axis=1)

    GHGs.loc[:, 'GWh_TOTAL'] = GHGs.loc[:, 'MMBtu_TOTAL']/3412.14

    GHGs.loc[:, 'TJ_TOTAL'] = GHGs.loc[:, 'GWh_TOTAL'] * 3.6

    GHGs.dropna(axis=1, how='all', inplace=True)

    return GHGs
    

def energy_merge(ghgrp_energy, all_fac, df_AA_energy):
    
    merge_cols = list(all_fac.columns.difference(df_AA_energy.columns))

    merge_cols.append('FACILITY_ID')

    df_AA_energy = pd.merge(
        df_AA_energy, all_fac[merge_cols], how='inner', on='FACILITY_ID'
        )
    
    ghgrp_energy = pd.concat([ghgrp_energy, df_AA_energy], ignore_index=True)
    
    return ghgrp_energy


def id_industry_groups(GHGs):
    """
    Assign industry groupings based on NAICS codes 
    """
    grouping_dict = {
        'Agriculture': [111,115], 'Mining and Extraction': [211, 212, 213], 
        'Utilities': 221, 'Construction': [236, 237, 238], 
        'Food Manufacturing': 311, 'Beverage Manufacturing':312, 
        'Textile Mills': 313, 'Textile Product Mills': 314,
        'Wood Product Manufacturing': 321, 'Paper Manufacturing': 322,
        'Printing': 323, 'Petroleum and Coal Products': 324,
        'Chemical Manufacturing': 325, 'Plastics and Rubber Products': 326,
        'Nonmetallic Mineral Products': 327, 'Primary Metals': 331,
        'All other Manufacturing': [332, 333, 334, 335, 336, 337, 338, 339],
        'Wholesale Trade': [423, 424,425],
        'Retail Trade': [441, 442, 443, 444, 445, 446, 447, 448, 451, 452,453,
         454], 'Transportation and Warehousing': [481, 482, 483,484, 485, 
         486, 487, 488,491, 492, 493], 'Publishing': [511, 512, 515, 517, 518,
         519],'Finance and Insurance': [521, 522, 523, 524, 525], 
        'Real Estate and Leasing': [531, 532, 533], 
        'Professional, Scientific, and Technical Services': 541, 
        'Management of Companies': 551, 
        'Admini and Support and Waste Management and Remediation Services': 
        [561, 562], 'Educational Services': 611, 
        'Health Care and Social Assistance': [621, 622, 623, 624], 
        'Arts and Entertainment': [711, 712, 713], 
        'Accommodation and Food Services': [721, 722],'Other Services': [811, 
        812, 813, 814], 'Public Adminsitration': [921, 
        922, 923, 924, 925, 926, 927, 928]
        }

    gd_v = []

    gd_k = []

    for v in list(grouping_dict.values()):

        kname = [k for k in grouping_dict if grouping_dict[k] == v][0]

        if type(v) == int:

            gd_v.append(v)

            gd_k.append(kname)

        else:

            gd_v.extend(w for w in v)

            gd_k.extend(kname for w in v)

    gd_df = pd.DataFrame(columns=('PNC_3', 'GROUPING'))

    gd_df.PNC_3 = gd_v

    gd_df.GROUPING = gd_k

    gd_df.set_index('PNC_3', inplace = True)

    GHGs['PNC_3'] = \
        GHGs['PRIMARY_NAICS_CODE'].apply(lambda n: int(str(n)[0:3]))

    GHGs = pd.merge(GHGs, gd_df, left_on = GHGs.PNC_3, right_index=True)

    #Identify manufacturing groupings
    gd_df['MFG'] = \
        gd_df.GROUPING.apply(
            lambda x: x in [gd_df.loc[i, :].values[0] for i in gd_df.index if
            str(i)[0] == '3']
            )

    gd_df['IND'] = gd_df.GROUPING.apply(
	    lambda x: x in [gd_df.loc[i,:].values[0] for i in gd_df.index if 
		   ((str(i)[0] == '3') | (str(i)[0] == '1') | ((str(i)[0] == '2') & \
            (str(i) != '221')))]
            )

    GHGs_E_dict = {}

    GHGs_GHG_dict = {}

    g_names = ['Ind_' + str(GHGs.REPORTING_YEAR.drop_duplicates().values[0])]

    for g_n in g_names:

        GHGs_GHG_dict[g_n] = \
            pd.DataFrame(
                GHGs[(GHGs['REPORTING_YEAR'] == int(g_n[-4:])) & 
                    (GHGs['CO2e_TOTAL'] > 0)]
                )

        GHGs_E_dict[g_n] = \
            pd.DataFrame(
                GHGs[(GHGs['REPORTING_YEAR']==int(g_n[-4:])) & 
                    (GHGs['MMBtu_TOTAL'] > 0)]
                )
                
    return GHGs

#
#GHGs = format_GHGRP_emissions(c_fuel_file, d_fuel_file)
#
#facdata = format_GHGRP_facilities(facilities_file)
#
#GHGs = calculate_energy(GHGs, facdata, EFs)
#
#GHGs = id_industry_groups(GHGs)
#
#GHGs.to_csv('ghgrp_energy_' + str(year) + '.csv')
