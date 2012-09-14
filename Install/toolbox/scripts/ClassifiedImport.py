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
    
def main(input_csv=None, sr=None, output_loc=None,
    output_gdb=None, output_fc=None, genetics=None,
    identification=None, loc=None, other=None,
    mode='toolbox'):

try: 
    
# if the script is running within ArcGIS as a tool, get the following user defined parameters:  
        
        # The input file in the SRDG.csv file format
        Parameter1 = parameters[0].valueAsText
        
        # A temporary XY Layer needed to create the feature class. 
        # NOTE: This file is deleted automatically when the script finishes
        Parameter2 = "TempXYLayer"                   
        
        # The spatial reference for the data (i.e. GCS_WGS84)
        Parameter3 = parameters[1].valueAsText   
      
        # The location of the File Geodatabase that will be created
        Parameter4 = parameters[2].valueAsText     
        
        # The name of the File Geodatabase
        Parameter5 = parameters[3].valueAsText  
     
        # The name of the Output Feature Class that will be created
        Parameter6 = parameters[4].valueAsText     
        
except:
    print ("Error setting tool parameters")
    print arcpy.GetMessages()
        
print "Parameters successfully defined"
    
try:
    # Process: Make XY Event Layer.  This layer is temporary and will be deleted upon script completion.
    # SYNTAX: arcpy.MakeXYEventLayer_management(table, in_x_field, in_y_field, out_layer, {spatial_reference}, {in_z_field})
    arcpy.MakeXYEventLayer_management(Parameter1, "Longitude", "Latitude", Parameter2, Parameter3, "")

except:
    print ("Error making XY Event Layer")
    print arcpy.GetMessages()
            
print ("XY event layer successfully created")


try:
    
    # Process: Create File GDB
    # SYNTAX: CreateFileGDB_management (out_folder_path, out_name, {out_version})
    arcpy.CreateFileGDB_management(Parameter4, Parameter5, "CURRENT")

except:
    print ("Error creating File GDB")
    print arcpy.GetMessages()    
    
print "File GDB successfully created"

try:
    # Process: Copy Features
    # SYNTAX: CopyFeatures_management (in_features, out_feature_class, {config_keyword}, {spatial_grid_1}, {spatial_grid_2}, {spatial_grid_3})
    arcpy.CopyFeatures_management(Parameter2, Parameter4 + '\\' + Parameter5 + '.gdb\\' + Parameter6, "", "0", "0", "0")

except:
    print ("Error copying features to a feature class")
    print arcpy.GetMessages() 
    
print "Feature Class successfully created"
print "Step 1 is done!"

# when executing as a standalone script get parameters from sys
if __name__=='__main__':

    # Dori's defaults when no configuration is provided
    defaults = {
      'input_csv':
        "C:\\geneGIS\\WorkingFolder\\SRGD_Photo_GeneSPLASH_CentAM_CA_OR_Feb12_v3.csv",
      'sr':
      "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',
       SPHEROID['WGS_1984',6378137.0,298.257223563]],
       PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400
      -400 1000000000;-100000 10000;-100000
      10000;8.98315284119521E-09;0.001;0.001;IsHighPrecision",
      'output_loc': "C:\\geneGIS\\WorkingFolder",
      'output_gdb': "PG_SPLASH_Subset2" 
      'output_fc': "TestFC"
    }

    inputs = ['input_csv', 'sr', 'output_loc', 'output_gdb',
    'output_fc', 'genetics', 'identification', 'loc', 'other']
    args = len(sys.argv) - 1
    # set any missing parameters with the default values from above
    for i, in_arg in enumerate(inputs):
        idx = i + 1
        # if we can't find the argument in question, set from our defaults
        if args < idx and idx <= 5:
            sys.argv[idx] = defaults[in_arg]
        # these dynamic attribute lists are for toolbox specific use.
        if idx >= 6:
            sys.argv[idx] = None
    
    main(input_csv=sys.argv[1],
        sr=sys.argv[2],
        output_loc=sys.argv[3],
        output_gdb=sys.argv[4],
        output_fc=sys.argv[5],
        genetics=sys.argv[6],
        identification=sys.argv[7],
        loc=sys.argv[8],
        other=sys.arvg[9],
        mode='script')
