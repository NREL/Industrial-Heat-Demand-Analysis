# -*- coding: utf-8 -*-
"""
Created on Fri Dec 29 11:44:46 2017

@author: cmcmilla
"""
from bs4 import BeautifulSoup

import pysal as ps

class CountyEnergy_Maps(object):
    """
    Create county-level chloropleths based on data identified by 
    state FIPS + county FIPS.
    """


    def __init__(self, county_file):
        self.svg = open(
            'U:\\Industrial Heat Survey\\Paper Version\Data and analysis\\' + \
            'Data for calculations\\USA_Counties_with_FIPS_and_names.svg', 'r'
            ).read()

        #Map colors. Example using http://colorbrewer2.org/.
        self.color_bins_hex = {
            #5: ['#feebe2','#fbb4b9','#f768a1','#c51b8a','#7a0177'],
            #7: ['#feebe2','#fcc5c0','#fa9fb5','#f768a1','#dd3497','#ae017e','#7a0177']
            7: ['#f0f9e8','#ccebc5','#a8ddb5','#7bccc4','#4eb3d3','#2b8cbe','#08589e'], \
            5: ['#f0f9e8','#bae4bc','#7bccc4','#43a2ca','#0868ac']
            }

        # colors7_rgb = [(240,249,232), (204,235,197),(168,221,181), \
        #     (123,204,196),(78,179,211),(43,140,190),(8,88,158)]

        #path_style2 = "opacity:1;fill:#d0d0d0;fill-opacity:1;fill-rule:nonzero;stroke:#000000;stroke-width:0.178287"
        self.path_style = 'font-size:12px;fill-rule:nonzero;stroke:#000;stroke-opacity:1;stroke-width:0.1;stroke-miterlimit:4;stroke-dasharray:none;stroke-linecap:butt;marker-start:none;stroke-linejoin:bevel;fill:'

        self.county_data = county_file

        self.county_data.set_index('COUNTY_FIPS', drop = True, inplace = True)

        self.data_dict = self.county_data.to_dict(orient = 'dict')


    def make_map(self, variable, nbins, preset_bins=None):
        """
        Saves map to working directory as .svg.
        """

        soup = BeautifulSoup(
            self.svg, selfClosingTags = ['defs', 'sodipodi: namedview']
            )

        paths = soup.findAll('path')
        
        if preset_bins == None:

            data_FJ = ps.Fisher_Jenks(  
                self.county_data[variable].fillna(0), k = nbins
                )
        
        else:
            
            data_FJ = preset_bins

        for p in paths:
             
            if p['id'] not in ["State_Lines", "separator"]:
                try:
                    value = self.data_dict[variable][int(p['id'])]
                except:
                    continue
                     
                for n in range(int(nbins) - 2, -1, -1):
                    if value > data_FJ.bins[n]:
                        color_class = n + 1
                        break
                    else:
                        color_class = 0
         
                color = self.color_bins_hex[nbins][color_class]

                p['style'] = self.path_style + color

        mapfile = 'map_' + variable + '.svg'

        with open(mapfile, 'w') as file:
            file.write(soup.prettify())