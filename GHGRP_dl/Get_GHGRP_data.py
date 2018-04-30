# -*- coding: utf-8 -*-
"""
Last updated 7/27/2017 by Colin McMillan, colin.mcmillan@nrel.gov
"""
#
import pandas as pd
import requests
import xml.etree.ElementTree as et

def xml_to_df(xml_root, table_name, df_columns):
    """
    Converts elements of xml string obtained from EPA envirofact (GHGRP)
    to a DataFrame.
    """
    rpd = pd.DataFrame()
    
    for c in df_columns:
        
        cl = []
        
        for field in xml_root.findall(table_name):
            
            cl.append(field.find(c).text)
            
        cs = pd.Series(cl, name = c)
   
        rpd = pd.concat([rpd, cs], axis = 1)
    
    return rpd

def get_GHGRP_records(reporting_year, table, rows = None):
    """
    Return GHGRP data using EPA RESTful API based on specified reporting year 
    and table. Tables of interest are C_FUEL_LEVEL_INFORMATION, 
    D_FUEL_LEVEL_INFORMATION, c_configuration_level_info, and 
    V_GHG_EMITTER_FACILITIES.
    Optional argument to specify number of table rows.
    """
    if table[0:14] == 'V_GHG_EMITTER_':
        table_url = 'https://iaspub.epa.gov/enviro/efservice/' + \
            table + '/YEAR/' + str(reporting_year)
    else:
        table_url = 'https://iaspub.epa.gov/enviro/efservice/' + \
            table + '/REPORTING_YEAR/' + str(reporting_year)

    r_columns = requests.get(table_url + '/rows/0:1')

    r_columns_root = et.fromstring(r_columns.content)

    clist = []
    
    for child in r_columns_root[0]:
        clist.append(child.tag)

    ghgrp = pd.DataFrame(columns = clist)

    if rows is None:
        try:
            r = requests.get(table_url + '/count/')
            nrecords = int(et.fromstring(r.content)[0].text)
        except:
            r.raise_for_status()

        if nrecords > 10000:
            
            rrange = range(0, nrecords, 10000)
            
            for n in range(len(rrange) - 1):

                try:
                    r_records = requests.get(table_url + '/rows/' + \
                        str(rrange[n]) + ':' + str(rrange[n + 1]))

                    records_root = et.fromstring(r_records.content)

                    r_df = xml_to_df(records_root, table, ghgrp.columns)

                    ghgrp = ghgrp.append(r_df)

                except:
                    r_records.raise_for_status()

            records_last = \
                requests.get(table_url + '/rows/' + str(rrange[-1]) + \
                    ':' + str(nrecords))

            records_lroot = et.fromstring(records_last.content)

            rl_df = xml_to_df(records_lroot, table, ghgrp.columns)

            ghgrp = ghgrp.append(rl_df)

        else:

            try:
                r_records = \
                    requests.get(table_url + '/rows/0:' + str(nrecords))

                records_root = et.fromstring(r_records.content)

                r_df = xml_to_df(records_root, table, ghgrp.columns)
            
                ghgrp = ghgrp.append(r_df)
            
            except:
                r_records.raise_for_status()
        

    
    else:
        try:
            r_records = requests.get(table_url + '/rows/0:' + str(rows))
            
            records_root = et.fromstring(r_records.content)
            
            r_df = xml_to_df(records_root, table, ghgrp.columns)
            
            ghgrp = ghgrp.append(r_df)
            
        except:
            r_records.raise_for_status()
       
    ghgrp.drop_duplicates(inplace = True)
    
    return ghgrp

    
#for t in ['V_GHG_EMITTER_FACILITIES']:
#    year = 2015
#    df = get_GHGRP_records(year, t)
#    df.to_csv(t[0:7] + '_' + str(year) + '.csv', index = False)
