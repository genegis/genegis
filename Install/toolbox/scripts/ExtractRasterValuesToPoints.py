# ---------------------------------------------------------------------------
# ExtractRasterValuesToPoints.py
#
# Created by: Dori Dick
#             College of Earth, Ocean and Atmospheric Sciences
#             Oregon State Univeristy
# 
# Created on: 3 March 2012
# Last modified: 9 September 2012
# 
# Description: This script converts spatially reference genetic data from a 
# simple flat file format to a Feature Class viewable in ArcGIS 10.  
#
# Required Inputs: Spatially referenced genetic data formatted according to 
# the SRDG.csv file format. This data can be for indentifed individuals or 
# for genetic samples.
#
# Optional Inputs: 
#   - If known, a spatial reference for the point data (recommended)
#
# Script Outputs: 
#   - a new File Geodatabase
#   - a new feature class located within the File Geodatabase
#
# This script was developed and tested on ArcGIS 10.1 and Python 2.7.
# ---------------------------------------------------------------------------

import arcpy
import os
import sys

# local imports
import utils
import config

def main(input_raster=None, selected_layer=None, output_ft=None, 
         mode=config.settings.mode):

        utils.msg("Executing ExtractRasterValuesToPoints.")   
        arcpy.CheckOutExtension("Spatial")
            
        # create a value table, prefix all output rasters with 'R_'
        rasters = input_raster.split(";")
        value_table = []
        for raster in rasters:
            # default name is just the label, prepend 'R_'
            (label, input_ext) = os.path.splitext(os.path.basename(raster))
            label = "R_{0}".format(label)
            value_table.append([raster, label])
        utils.msg("generated value table: %s" % value_table)
        utils.msg("Running ExtractMultiValuesToPoints...")
        arcpy.sa.ExtractMultiValuesToPoints(selected_layer, value_table, "NONE")
        utils.msg("Values successfully extracted")  
          
# when executing as a standalone script get parameters from sys
if __name__=='__main__':

    # Defaults when no configuration is provided
    # TODO: change these to be test-based.
    defaults_tuple = (
        ('input_table',
        "C:\\geneGIS\\WorkingFolder\\SRGD_Photo_GeneSPLASH_CentAM_CA_OR_Feb12_v3.csv"),
        ('sr', DEFAULT_SR),
    )

    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(*defaults.values(), mode='script')
