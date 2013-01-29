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

# local imports
import utils
import config

def main(input_table=None, sr=None, output_loc=None,
    output_gdb=None, output_fc=None, genetic=None,
    identification=None, location=None, other=None,
    mode=config.mode):

    # First, create a geodatabase for all our future results.
    # TODO: can we generate this from a single value?
    gdb_path = os.path.abspath(os.path.join(output_loc, output_gdb + '.gdb'))

    # check if we received a value spatial reference -- if not, use WGS84.
    if sr in ('', None):
        # default spatial reference can be redefined.
        sr = config.DEFAULT_SR

    try:
        # only try to create this GDB if it doesn't already exist.
        if not os.path.exists(gdb_path):
            # Process: Create File GDB
            # SYNTAX: CreateFileGDB_management (out_folder_path, out_name, {out_version})
            arcpy.CreateFileGDB_management(output_loc, output_gdb, "CURRENT")
    except Exception as e:
        utils.msg("Error creating File GDB", mtype='error', exception=e)
        
    utils.msg("File GDB successfully created")

    # TODO: WE NEED TO DO A FULL CLASSIFICATION OF THE INPUT AND MANUALLY BUILD UP THE LAYER...
    # We'll have two columns per locus, need to import correctly

    # Start things off by importing the table directly. We still need to edit the header
    # because of ArcGIS' restrictions on table names.

    # do we have a text-based file?
    file_type = utils.file_type(input_table)
    if file_type == 'Text':
        # Generate a temporary copy of the input CSV which corrects it for 
        # ArcGIS, stripping invalid column label characters.
        data_table = validate_table(input_table)
    else:
        data_table = input_table 
    # OPTIONS:
    # arcpy.CopyRows_management("my_table.csv", "c:\\my.gdb\my_table")
    # COPY ROWS will add an Object ID field; table to table WILL NOT.
    # arcpy.TableToTable_conversion (in_rows, out_path, out_name, {where_clause}, {field_mapping}, ...)
   
    # TODO: use field mapping to handle the date-time field?
    # write out our table to the newly created GDB.
    try:
        arcpy.env.overwriteOutput = config.overwrite
        
        # generate table name based on input name
        (label, ext) = os.path.basename(input_table)
       
        # write out our filtered table to ArcGIS
        arcpy.TableToTable_conversion(data_table, gdb_path, label)

    except Exception as e:
        utils.msg("Error converting table %s to GDB" % input_table, mtype='error', exception=e)

    # Convert the table to a temporary spatial feature
    try:

        input_csv = os.path.join([gdb_path, label)]

        # A temporary XY Layer needed to create the feature class. 
        # NOTE: This table is deleted when the script finishes
        temporary_layer = os.path.join([input_csv, '_xy_temp'])

        # 'location', ArcGIS passes semicolon separated values
        (x, y) = location.split(";")

        # Process: Make XY Event Layer.  This layer is temporary and will be 
        # deleted upon script completion.
        # SYNTAX: arcpy.MakeXYEventLayer_management(table, in_x_field, 
        #           in_y_field, out_layer, {spatial_reference}, {in_z_field})
        arcpy.MakeXYEventLayer_management(input_csv, x, y, temporary_layer, sr)
    except Exception as e:
        utils.msg("Error making XY Event Layer", mtype='error', exception=e)
    
    utils.msg("XY event layer successfully created: \n %s" % temporary_layer)
  
    # Copy our features to a permanent layer
    try:
        fc_path = os.path.join(gdb_path, output_fc)
        # for this step, overwrite any existing results
        arcpy.env.overwriteOutput = config.overwrite

        # Process: Copy Features
        # SYNTAX: CopyFeatures_management (in_features, out_feature_class, {config_keyword}, {spatial_grid_1}, {spatial_grid_2}, {spatial_grid_3})
        arcpy.CopyFeatures_management(temporary_layer, fc_path, "", "0", "0", "0")
    except Exception as e:
        utils.msg("Error copying features to a feature class", mtype='error', exception=e)
   
    try:
        arcpy.Delete_management(temporary_layer)
    except Exception as e:
        utils.msg("Unable to delete temporary layer", mtype='error', exception=e)

   
    # finally, convert the imported feature into a new geometry
    try:
        fc_path = os.path.abspath(os.path.join(gdb_path, output_fc))
        # for this step, overwrite any existing results
        arcpy.env.overwriteOutput = config.overwrite

        # Process: Copy Features
        # SYNTAX: CopyFeatures_management (in_features, out_feature_class, {config_keyword}, {spatial_grid_1}, {spatial_grid_2}, {spatial_grid_3})
        arcpy.CopyFeatures_management(temporary_layer, fc_path, "", "0", "0", "0")
    except Exception as e:
        utils.msg("Error copying features to a feature class", mtype='error', exception=e)
   
    try:
        arcpy.Delete_management(temporary_layer)
    except Exception as e:
        utils.msg("Unable to delete temporary layer", mtype='error', exception=e)

    utils.msg("Feature Class successfully created, your SRGD file has been imported!")



    utils.msg("Feature Class successfully created, your SRGD file has been imported!")

# when executing as a standalone script get parameters from sys
if __name__=='__main__':

    # Defaults when no configuration is provided
    # TODO: change these to be test-based.
    defaults_tuple = (
        ('input_table',
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

    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(*defaults.values(), mode='script')
