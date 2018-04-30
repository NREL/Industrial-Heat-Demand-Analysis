# -*- coding: utf-8 -*-
"""
Created on Wed Aug 30 07:46:40 2017

@author: cmcmilla
"""

import pandas as pd

import numpy as np


def ti_format(ghgrp_energy_file, target_ind_file):
    """
    Identify facilities that reported a primary or secondary NAICS code that
    matches the list of 14 'target industries' identified by
    McMillan et al. (2016)
    """
    ghgrp_energy = pd.read_csv(ghgrp_energy_file, encoding='latin1')

    ghgrp_energy.reset_index(drop=True, inplace=True)

    targetind = pd.read_csv(target_ind_file, index_col='NAICS')

    ghgrp_energy.SECONDARY_NAICS_CODE.fillna(0, inplace=True)

    ghgrp_energy.loc[:, 'SECONDARY_NAICS_CODE'] = \
        ghgrp_energy.SECONDARY_NAICS_CODE.astype(np.int64)

    target_201015 = pd.DataFrame(
        ghgrp_energy[(ghgrp_energy.PRIMARY_NAICS_CODE.apply(
            lambda x: x in targetind.index
            )) | (ghgrp_energy.SECONDARY_NAICS_CODE.apply(
                lambda x: x in targetind.index
                ))]
        )

    # Create new column 'FINAL_NAICS_CODE' with NAICS code selected to
    # represent the production activities of each facility identified as being
    # part of the 'target industries'. Identification based on either reported
    # primary or secondary NAICS code.
    target_201015.loc[:, 'FINAL_NAICS_CODE'] = 0

    target_201015.FINAL_NAICS_CODE.update(
        target_201015[(target_201015.PRIMARY_NAICS_CODE.apply(
            lambda x: x not in targetind.index
            )) & (target_201015.SECONDARY_NAICS_CODE.apply(
                lambda x: x in targetind.index
                ))
                   ].SECONDARY_NAICS_CODE
        )

    target_201015.FINAL_NAICS_CODE.update(
        target_201015[(target_201015.PRIMARY_NAICS_CODE.apply(
            lambda x: x in targetind.index
            )) & (target_201015.SECONDARY_NAICS_CODE.apply(
                lambda x: x not in targetind.index
                ))
                   ].PRIMARY_NAICS_CODE
        )
    
    target_201015.FINAL_NAICS_CODE.update(
        target_201015[(target_201015.PRIMARY_NAICS_CODE.apply(
            lambda x: x in targetind.index
            )) & (target_201015.SECONDARY_NAICS_CODE.apply(
                lambda x: x in targetind.index
                ))
                   ].PRIMARY_NAICS_CODE
        )
        
    # Converting MMBtu to TJ
    target_201015.loc[:, 'TJ'] = target_201015.MMBtu_TOTAL * 0.001055
    
    return target_201015