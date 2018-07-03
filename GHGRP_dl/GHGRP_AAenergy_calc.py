# -*- coding: utf-8 -*-
"""
Created on Wed Aug 30 09:52:53 2017

@author: cmcmilla
"""
import pandas as pd


def format_GHGRP_AAff_emissions(aa_ffuel_file):
    """
    Format Subpart AA fossil fuel combustion emissions.
    """
    GHGs_FF = pd.read_csv(
       aa_ffuel_file, encoding='latin_1', index_col=0, low_memory=False
        )

    GHGs_FF.dropna(axis=0, subset=['FACILITY_ID'], inplace=True)

    GHGs_FF.reset_index(drop=True, inplace=True)

    for c in ('FACILITY_ID', 'REPORTING_YEAR'):

        GHGs_FF.loc[:, c] = [int(x) for x in GHGs_FF[c]]

    GHGs_FF.loc[:, 'CO2e_TOTAL'] = 0

    total_co2 = pd.DataFrame()

    for tier in ['TIER_1_', 'TIER_2_', 'TIER_3_']:

        for ghg in ['CH4_EMISSIONS_CO2E', 'N2O_EMISSIONS_CO2E',
            'CO2_EMISSIONS']:

            total_co2 = pd.concat([total_co2, GHGs_FF[tier + ghg]], axis=1)

    total_co2.fillna(0, inplace=True)

    GHGs_FF.loc[:, 'CO2e_TOTAL'] = total_co2.sum(axis=1)

    return GHGs_FF


def format_GHGRP_AAsl_emissions(aa_sl_file):
    """
    Format Subpart AA spent liquor (sl) combustion emissions.
    """
    GHGs_SL = pd.read_csv(
       aa_sl_file, encoding='latin_1', index_col=0, low_memory=False
        )

    GHGs_SL.reset_index(drop=True, inplace=True)

    GHGs_SL.dropna(axis=0, subset=['SPENT_LIQUOR_CO2_EMISSIONS'], inplace=True)

    for c in ('FACILITY_ID', 'REPORTING_YEAR'):

        GHGs_SL.loc[:, c] = [int(x) for x in GHGs_SL[c]]

    GHGs_SL.loc[:, 'FUEL_TYPE'] = 'Wood and Wood Residuals'
    
    total_co2 = pd.DataFrame()

    for g in ['CO2_EMISSIONS', 'CH4_EMISSIONS', 'N2O_EMISSIONS']:

        total_co2 = pd.concat([total_co2, GHGs_SL['SPENT_LIQUOR_' + g]],
                              axis=1)

        total_co2.fillna(0, inplace=True)

    GHGs_SL.loc[:, 'CO2e_TOTAL'] = total_co2.sum(axis=1)

    return GHGs_SL


def MMBTU_calc_AAff(GHGs_FF, EFs):
    """
    Calculate MMBtu value based on reported CO2 emissions.
    Does not capture emissions and energy from facilities using Tier 4
    calculation methodology.
    """
    # Drop facilities that do not report a fuel type.
    GHGs_FF.dropna(subset=['FUEL_TYPE'], inplace=True) 

    df_FF_energy = pd.DataFrame(index=GHGs_FF.index)

    for c in ['TIER_1_CO2_EMISSIONS', 'TIER_2_CO2_EMISSIONS',
        'TIER_3_CO2_EMISSIONS']:

        for ft in GHGs_FF['FUEL_TYPE'].drop_duplicates():

            fuel_index = GHGs_FF[
                (GHGs_FF.FUEL_TYPE == ft) & (GHGs_FF[c].notnull())
                ].index

            if fuel_index.size > 0:

                df_FF_energy.loc[fuel_index, (c[0:6] + '_MMBtu')] = \
                    GHGs_FF.loc[fuel_index, c].divide(
                        EFs.ix[ft]['CO2_kgCO2_per_mmBtu'], fill_value=0
                        )
            else:
                pass

    df_FF_energy.loc[:, 'MMBtu_TOTAL'] = df_FF_energy.sum(axis=1)

    df_FF_energy.drop(['TIER_1_MMBtu', 'TIER_2_MMBtu', 'TIER_3_MMBtu'],
        axis=1, inplace=True)

    df_FF_energy = pd.concat([GHGs_FF[[
        'FACILITY_ID', 'REPORTING_YEAR', 'FACILITY_NAME', 'UNIT_NAME',
        'FUEL_TYPE', 'CO2e_TOTAL'
        ]], df_FF_energy], axis=1)

    return df_FF_energy


def MMBTU_calc_AAsl(GHGs_SL):
    """
    Calculate MMBtu value based on CH4 emissions reported under Tier 4.
    """
    df_sl_energy = pd.DataFrame(GHGs_SL)

    df_sl_energy.loc[:, 'MMBtu_TOTAL'] = \
        df_sl_energy.SPENT_LIQUOR_CH4_EMISSIONS.divide(
            df_sl_energy.BIOMASS_CH4_EMISSIONS_FACTOR)

    df_sl_energy.MMBtu_TOTAL.update(
        df_sl_energy[
            df_sl_energy.MMBtu_TOTAL.isnull()
            ].SPENT_LIQUOR_CH4_EMISSIONS.divide(0.0072)
        )

    df_sl_energy.drop([
        'SPENT_LIQUOR_CO2_EMISSIONS', 'SPENT_LIQUOR_CH4_EMISSIONS',
        'SPENT_LIQUOR_N2O_EMISSIONS', 'BIOMASS_CH4_EMISSIONS_FACTOR',
        'BIOMASS_N2O_EMISSIONS_FACTOR'
        ], axis=1, inplace=True)

    return df_sl_energy


def AA_merge(df_FF_energy, df_sl_energy):
    """
    Merge resuts of Subpart AA energy calculations into a single dataframe.
    """

    df_AA_energy = df_FF_energy.append(df_sl_energy, ignore_index=False)

    df_AA_energy.reset_index(drop=True, inplace=True)

    return df_AA_energy
    
    