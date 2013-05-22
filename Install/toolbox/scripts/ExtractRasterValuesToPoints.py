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
import binascii

# local imports
import utils
import config

def main(input_raster=None, selected_layer=None, output_ft=None, 
         mode=config.settings.mode):

        utils.msg("Executing ExtractRasterValuesToPoints.")   
        arcpy.CheckOutExtension("Spatial")
        utils.msg("Checking out Spatial Analyst Extension.")
        arcpy.sa.ExtractMultiValuesToPoints(selected_layer, input_raster, "NONE")
        utils.msg("Values successfully extracted")  

        #arcpy.sa.Sample([input_raster], selected_layer, output_ft, "NEAREST")             
        #utils.msg(selected_layer)
        #utils.msg(output_ft)
        #arcpy.JoinField_management(selected_layer, "OBJECTID", output_ft, "GOA_Encounters_copy", "ETOPO1_clip")
        #arcpy.JoinField_management (in_data, in_field, join_table, join_field, {fields})
       
       
          
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
