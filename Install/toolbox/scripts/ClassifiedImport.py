# ---------------------------------------------------------------------------
# ClassifiedImport.py
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
import collections

DEFAULT_SR = ("GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',"
            "SPHEROID['WGS_1984',6378137.0,298.257223563]],"
            "PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400"
            "-400 1000000000;-100000 10000;-100000 "
            "10000;8.98315284119521E-09;0.001;0.001;IsHighPrecision")

def main(input_csv=None, sr=None, output_loc=None,
    output_gdb=None, output_fc=None, genetic=None,
    identification=None, location=None, other=None,
    mode='toolbox'):

    # A temporary XY Layer needed to create the feature class. 
    # NOTE: This file is deleted when the script finishes
    temporary_layer = binascii.b2a_hex(os.urandom(15))

    # check if we received a value spatial reference -- if not, use WGS 1984.
    if sr == None or sr == '':
        sr = DEFAULT_SR

    try:
        # Process: Make XY Event Layer.  This layer is temporary and will be deleted upon script completion.
        # SYNTAX: arcpy.MakeXYEventLayer_management(table, in_x_field, in_y_field, out_layer, {spatial_reference}, {in_z_field})
        arcpy.MakeXYEventLayer_management(input_csv, "Longitude", "Latitude", temporary_layer, sr, "")
    except:
        print "Error making XY Event Layer"
        print arcpy.GetMessages()
                
    print "XY event layer successfully created"
    
    gdb_path = os.path.join(output_loc, output_gdb + '.gdb')

    try:
        # only try to create this GDB if it doesn't already exist.
        if not os.path.exists(gdb_path):
            # Process: Create File GDB
            # SYNTAX: CreateFileGDB_management (out_folder_path, out_name, {out_version})
            arcpy.CreateFileGDB_management(output_loc, output_gdb, "CURRENT")
    except:
        print "Error creating File GDB"
        print arcpy.GetMessages()
        
    print "File GDB successfully created"

    try:
        fc_path = os.path.abspath(os.path.join(gdb_path, output_fc))
        # for this step, overwrite any existing results
        arcpy.env.overwriteOutput = True

        # Process: Copy Features
        # SYNTAX: CopyFeatures_management (in_features, out_feature_class, {config_keyword}, {spatial_grid_1}, {spatial_grid_2}, {spatial_grid_3})
        arcpy.CopyFeatures_management(temporary_layer, fc_path, "", "0", "0", "0")
    except:
        print "Error copying features to a feature class"
        print arcpy.GetMessages() 
   
    try:
        arcpy.Delete_management(temporary_layer)
    except:
        print "Unable to delete temporary layer"

    print "Feature Class successfully created"
    print "Step 1 is done!"

# when executing as a standalone script get parameters from sys
if __name__=='__main__':

    # Dori's defaults when no configuration is provided
    defaults_tuple = (
        ('input_csv',
        "C:\\geneGIS\\WorkingFolder\\SRGD_Photo_GeneSPLASH_CentAM_CA_OR_Feb12_v3.csv"),
        ('sr', DEFAULT_SR),
        ('output_loc', "C:\\geneGIS\\WorkingFolder"),
        ('output_gdb', "PG_SPLASH_Subset2"),
        ('output_fc', "TestFC"),
        ('genetic', None),
        ('identification', None),
        ('location', None),
        ('other', None),
    )

    defaults = collections.OrderedDict(defaults_tuple)
    args = len(sys.argv) - 1
    for i, key in enumerate(defaults.keys()):
        idx = i + 1
        if idx <= args:
            defaults[key] = sys.argv[idx]

    main(*defaults.values(), mode='script')
