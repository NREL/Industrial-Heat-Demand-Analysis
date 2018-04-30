# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 15:32:38 2018

@author: cmcmilla
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
from textwrap import wrap

def AltES_Sizing(target_char, plot_load_figs=False):
    """
    Method for assigning an alternative energy supply to individual
    facilities based on calculated heat load in MW and temperature.
    """
    # assumed temp and load characteristics of alt energy generators
    char = {'Geo': {'t_max': 150, 'load': [0.001, 100]},
                   'SIPH': {'t_max': 1000, 'load': [0.001, 200]},
                   'SMR': {'t_max': 850, 'load': [100, 600]}
                   }

    # assumed annual operating hours (8760*90%)
    op_hours = 7800

    # Account for the fact that many pulp and paper facilities use fossil
    # fuels in addition to byproduct combustion. 
    bypm_i1 = target_char[(target_char.Biogenic == False) &
                        (target_char.Pulp_Paper == True)].index

    bypm_i2 = target_char[target_char.Process_byp == False].index

    for i in [bypm_i1, bypm_i2]:

        target_char.loc[i, 'Byp_match'] = True

    target_char.Byp_match.fillna(False, inplace=True)

    # Calculate annual load for each facility (in MW). 
    # 'All' includes all faciliites, including those that use process
    # byproducts as combustion. 'Alt' excludes byproduct combusion at
    # byproduct-reliant facilities (i.e., where Byp_match == True)
    load_MW = {}

    for k in ['All', 'Alt']:

        if k == 'All':

            load_MW[k] = \
                pd.DataFrame(
                    target_char.groupby(
                        ['REPORTING_YEAR', 'FACILITY_ID', 'Temp_degC']
                        ).Total.sum()
                    )

        else:

            load_MW[k] = \
                pd.DataFrame(
                    target_char[target_char.Byp_match==True].groupby(
                        ['REPORTING_YEAR', 'FACILITY_ID', 'Temp_degC']
                        ).Total.sum()
                    )

        load_MW[k].rename(columns={'Total': 'Total_TJ'}, inplace=True)

        load_MW[k].loc[:, 'MW'] = load_MW[k].Total_TJ*277.777778/op_hours

    # Plot heat load curve
    def DemandCurve(matched=True, dtype='load'):
        """
        Plot curve for either load (MW) or energy (TJ) for all available years.
        """
        y_colors = ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e',
                    '#e6ab02']

        if dtype == 'load':
            data = 'MW'
            x_label2 = ' Load (GW-thermal)'
            x_lim = [0, 250]

        if dtype == 'energy':
            data = 'Total_TJ'
            x_label2 = ' Energy (PJ)'
            x_lim = [0, 6000]

        if matched == True:
            df = load_MW['Alt']
            x_label1 = 'Alt Heat-Matched'

        if matched == False:
            df = load_MW['All']
            x_label1 = 'All'

        with plt.rc_context(dict(sns.axes_style("whitegrid"),
                         **sns.plotting_context('talk'))
                        ):

            nc = 0

            fig, ax = plt.subplots()

            for y in df.index.levels[0].values:

                curve_x= df.loc[y].reset_index().sort_values(
                    'Temp_degC', ascending=True
                    )[data].cumsum().values/1000
                curve_y = df.loc[y].reset_index().sort_values(
                    'Temp_degC', ascending=True
                    ).Temp_degC.values
                ax.plot(
                    curve_x, curve_y, y_colors[nc], linewidth=2.7, label=y
                    )

                nc = nc + 1

            ax.legend()

            ax.set(
                xlabel=x_label1 + x_label2, ylabel='Temperature (Celcius)', 
                ylim=[0, 1600], xlim=x_lim
                )

            fig.savefig(
                'TempCurve_' + data + x_label1 + '.png', bbox_inches='tight',
                dpi=200
                )

            plt.close()

    if plot_load_figs == True:
  
        for tf in [True, False]:   
            DemandCurve(tf, 'load')
            DemandCurve(tf, 'energy')

    else:
        pass


    def load_calcs(selection):
        """
        Final load calulcations.
        """
        load = \
            pd.pivot_table(
                load_MW[selection].MW.reset_index(),
                           index='FACILITY_ID', columns='REPORTING_YEAR',
                           aggfunc=np.sum
                ).loc[:, ('MW')]

        load.loc[:, 'load_max'] = load.max(axis=1)

        load.loc[:, 't_max'] = \
            target_char.groupby('FACILITY_ID').Temp_degC.max()
            
        return load

    # Estimate maximum load for only byproduct-excluded facilities over
    # 2010 - 2015 period. 
    alt_load = load_calcs('Alt')

    # Estimate maximum load for all facilities over 2010 - 2015 period.
    all_load = load_calcs('All')

    # Match facility to alt supply based on temperature and load
    # Note facilities that would need >1 SMR (i.e., max load > 600).
    supply_match = pd.DataFrame(index=alt_load.index, columns=char.keys()) 

    for supply in char.keys():

        s_index = alt_load[
            (alt_load.load_max.between(
                char[supply]['load'][0], char[supply]['load'][1])) &
                (alt_load.t_max <= char[supply]['t_max'])
            ].index

        supply_match.loc[s_index, supply] = True

        if supply == 'SMR':

            smr_only_index = alt_load[
                (alt_load.load_max.between(
                    char['SIPH']['load'][1], char[supply]['load'][1]
                    )) & (alt_load.t_max <= char[supply]['t_max'])
                ].index

            supply_match.loc[smr_only_index, 'SMR_only'] = True
            
            supply_match.SMR_only.fillna(False, inplace=True)

    # Note facilities that are above temperature range of SMRs and above load
    # for CSP (i.e., temp > 850C & load > 600 MW)
    supply_match.loc[
        supply_match[supply_match[['Geo', 'SIPH', 'SMR']].isnull().all(axis=1)].index,
        'Load_Temp_match'] = False

    supply_match.Load_Temp_match.fillna(True, inplace=True)
    
    for supply in char.keys():
        
        supply_match[supply].fillna(False, inplace=True)

    # Add NAICS codes and descriptions
    n_dict = dict(target_char[['FACILITY_ID', 'FINAL_NAICS_CODE']].values)
    ndesc_dict = {212391: 'Potash Mining', 311221: 'Wet Corn Milling',
                  322110: 'Pulp Mills', 322121: 'Paper (except Newsprint)',
                  322130: 'Paperboard', 324110: 'Petroleum Refining',
                  325110: 'Petrochemicals', 325181: 'Alkalies and Chlorine',
                  325193: 'Ethyl Alcohol',
                  325199: 'All Other Basic Chemical Manufacturing (Methanol)',
                  325211: 'Plastics Material and Resin',
                  325311: 'Nitrogenous Fertilizer', 327410: 'Lime', 
                  331111: 'Iron and Steel'}

    for df in [alt_load, all_load, supply_match]:

        df.reset_index(inplace=True)

        df.loc[:, 'FINAL_NAICS_CODE'] = df['FACILITY_ID'].map(n_dict)

        df.set_index('FACILITY_ID', inplace=True)

        df.loc[:, 'NAICS_Desc'] = \
            df.FINAL_NAICS_CODE.apply(lambda x: ndesc_dict[x])

    return alt_load, all_load, supply_match


def MatchedSavings(supply_match, target_char):
    """
    Summarize GHG emissions savings and ff savings by fuel type for alt
    energy sources.
    Returns a dictionary of dataframes with ff savings and ghg savings by
    alt energy source.
    """
    ffuels = ['Coal', 'Diesel', 'LPG_NGL', 'Natural_gas',
              'Residual_fuel_oil', 'Other']

    supply_savings = {}

    target_char = pd.merge(
        target_char, pd.DataFrame(
            supply_match[['Load_Temp_match', 'SMR_only']]
            ), left_on='FACILITY_ID', right_index=True
        )

    # Final determination of whether combustion of a fuel at a facility is 
    # appropriate for substitution for an alt energy generator.

    fm_i = target_char[(target_char.Byp_match == True) &
                        (target_char.Load_Temp_match == True)].index

    target_char.loc[fm_i, 'Final_match'] = True

    target_char.Final_match.fillna(False, inplace=True)

    supply_ff = \
        target_char[target_char.Final_match == True].groupby(
                        ['FACILITY_ID', 'REPORTING_YEAR']
                        )[ffuels].sum()

    supply_ff.loc[:, 'Total'] = supply_ff.sum(axis=1)


    supply_ghg = \
        pd.DataFrame(target_char[target_char.Final_match == True].groupby(
                        ['FACILITY_ID', 'REPORTING_YEAR']
                        )['MMTCO2E'].sum())

    for df in [supply_ff, supply_ghg]:

        df.reset_index(inplace=True, level=1)

        pt = pd.DataFrame()

        for s in ['Geo', 'SIPH', 'SMR']:

            s_index = supply_match[supply_match[s] == True].index

            df.loc[s_index, s] = True

            df[s].fillna(False, inplace=True)

            if 'Coal' in df.columns:

                pt_vals = ffuels

                d_name = 'ff'

            else:

                pt_vals = None

                d_name = 'ghg'
                
            if s == 'SMR':
                
                smr_only_index = \
                    supply_match[supply_match.SMR_only == True].index
                    
                df.loc[smr_only_index, 'SMR_only'] = True
                
                pt = pt.append(pd.pivot_table(df[df.SMR_only == True], 
                               index=['SMR_only', 'REPORTING_YEAR'],
                               values=pt_vals, aggfunc=np.sum).rename(
                                   index={True: 'SMR_only'}
                                   )
                               )

            pt = pt.append(
                pd.pivot_table(df[df[s] == True], index=[s, 'REPORTING_YEAR'],
                    values=pt_vals, aggfunc=np.sum).rename(index={True: s})
                    )

        if pt_vals == None:

            pt = pd.DataFrame(pt['MMTCO2E'])

        pt.loc[:, 'Total'] = pt.sum(axis=1)

        df = pt

        supply_savings[d_name] = df

    return supply_savings, target_char


def DrawMatchPlot(supply_match, all_load, year):
    """
    Draw scatter plot of facilities by load and max temperature requirement,
    with bounds for SIPH, geo, SMR temps and loads.
    """
    char = {'Geo': {'t_max': 150, 'load': [0.001, 100]},
               'SIPH': {'t_max': 1000, 'load': [0.001, 200]},
               'SMR': {'t_max': 850, 'load': [100, 600]}
               }

    with plt.rc_context(dict(sns.axes_style("whitegrid"),
                         **sns.plotting_context('talk'))
                        ):

        loads = {}
        temps = {}

        industries = all_load.NAICS_Desc.drop_duplicates()

        e_colors = {'SIPH': '#fc8d62', 'Geo': '#66c2a5', 'SMR': '#8da0cb'}

        i_colors = sns.husl_palette(len(industries), l=0.6)

        nc = 0

        for industry in industries:

            loads[industry] = \
                all_load[
                    (all_load[year].notnull()) &
                    (all_load.NAICS_Desc == industry)
                    ].loc[:, year].values

            temps[industry] = \
                all_load[
                    (all_load[year].notnull()) &
                    (all_load.NAICS_Desc == industry)
                    ].loc[:, 't_max'].values

            ax2 = sns.regplot(
                loads[industry], temps[industry], fit_reg=False,
                label='\n'.join(wrap(industry, 20)), color=i_colors[nc]
                )

            nc = nc + 1

        for supply in char.keys():
            patch = patches.Rectangle(
                (char[supply]['load'][0], 0),
                char[supply]['load'][1] - char[supply]['load'][0],
                char[supply]['t_max'], fill=False, edgecolor=e_colors[supply],
                linewidth=2.5, label=supply
                )

            ax2.add_patch(patch)

        ax2.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)

        ax2.set(
            xlabel='Annual Average Load (MW-thermal)',
            ylabel='Max Temperature Demand (Celcius)', xscale='log', 
            xlim=(0.001, 6000), ylim=(0, 1600)
            )

        plt.savefig('SupplyMatching.png', bbox_inches='tight', dpi=200)
