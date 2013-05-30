# CalculateDistance.py: geodesic paths between points
# -*- coding: utf-8 -*-
# Created by: Shaun Walbridge
#             Esri

# Created on: 26 May 2013

#Shortest cost paths between all elements, in geographic space.

"""
A result between: (-83.7453,8.6583) and (-85.9176,11.0253): 353995.597 meters
The same calculation in geographiclib producees: 353995.597 meters
"""

import arcpy
import os
import sys

# local imports
import utils
import config
import time

def main(input_fc=None, output_fc=None, closest=False, mode=config.settings.mode):
    
    # convert 'closest' string value
    closest_count = ""
    if closest == 'true':
        closest_count = 1

    # does the input fc exist?
    if not arcpy.Exists(input_fc):
        utils.msg("Input, %s, doesn't exist.", mtype='error')
        sys.exit()

    input_fc_mem = 'in_memory/input_fc'
    try:
        utils.msg("Copying features into memory…")
        arcpy.CopyFeatures_management(input_fc, input_fc_mem)
    except Exception as e:
        utils.msg("Unable to copy features into memory.", mtype='error', exception=e)
        sys.exit()

    # add POINT_X and POINT_Y columns
    try:
        arcpy.AddXY_management(input_fc_mem)
    except Exception as e:
        message = "Error creating point coordinate values for {0}".format(input_fc)
        utils.msg(message, mtype='error', exception=e)
        sys.exit()

    # get the spatial reference of our input, determine the type
    desc = arcpy.Describe(input_fc_mem)
    sr = desc.spatialReference
    if sr.type not in ['Geographic', 'Projected']:
        utils.msg("This tools only works with geographic or projected data.", mtype='error')
        sys.exit()

    # yes, all this mucking about is necessary to get a row count
    row_count = int(arcpy.GetCount_management(input_fc_mem).getOutput(0))
    
    if row_count < 500 or closest:
        near_table = 'in_memory/near_table'
        output_fc_mem = 'in_memory/output_fc'
    else:
        utils.msg("Too many features (%i) to load pairwise into memory. Using disk, which decreases performance." % row_count)
        near_table = os.path.join(arcpy.env.scratchGDB, 'near_table')
        output_fc_mem = output_fc

    # create a look-up table which maps individual observations to all others.
    # FIXME: do we need to filter this in some way? by group, ...?
    try:
        # generates an output table with IN_FID, NEAR_FID, NEAR_X, NEAR_Y [...]
        utils.msg("Creating near table…")
        arcpy.GenerateNearTable_analysis(input_fc_mem, input_fc_mem, near_table, \
                "", "LOCATION", "NO_ANGLE", "ALL", closest_count)

        time.sleep(5)
    except Exception as e:
        utils.msg("Error creating near table.", mtype='error', exception=e)
        sys.exit()

    try:
        utils.msg("Joining attributes…")
        in_fields = arcpy.ListFields(input_fc_mem)
        # find the OID field.
        oid_field = [f.name for f in in_fields if f.type == 'OID'][0]

        # join back our 'true' x & y columns to the original data.
        arcpy.JoinField_management(near_table, "IN_FID", input_fc_mem, oid_field, ['POINT_X','POINT_Y'])
        # clean up
        arcpy.Delete_management(input_fc_mem)

        in_fields = arcpy.ListFields(near_table)
        oid_field = [f.name for f in in_fields if f.type == 'OID'][0]

        id_field = 'ID'
        # add an 'ID' field other than the OID so we can copy it over using XYToLine
        arcpy.AddField_management(near_table, id_field, "LONG")
        expression = "!{0}!".format(oid_field)
        arcpy.CalculateField_management(near_table, id_field, expression , "PYTHON_9.3")

    except Exception as e:
        utils.msg("Error joining data.", mtype='error', exception=e)
        sys.exit()

    # Now compute the lines between these locations.
    try:
        utils.msg("Computing pairwise geodesic lines…")
        arcpy.XYToLine_management(near_table, output_fc_mem, \
                "NEAR_X", "NEAR_Y", "POINT_X", "POINT_Y", "GEODESIC", id_field)

        utils.msg("Remapping output columns…")
        arcpy.JoinField_management(output_fc_mem, id_field, near_table, id_field, ['IN_FID', 'NEAR_FID'])

        # column modifications necessary
        remap_cols = [
          ('IN_FID', 'Source_ID', '!IN_FID!'),
          ('POINT_X', 'Source_X', '!POINT_X!'),
          ('POINT_Y', 'Source_Y', '!POINT_Y!'),
          ('NEAR_FID', 'Dest_ID', '!NEAR_FID!'), 
          ('NEAR_X', 'Dest_X', '!NEAR_X!'), 
          ('NEAR_Y', 'Dest_Y', '!NEAR_Y!'),
          (None, 'Distance_in_km', "!Shape.length@kilometers!") # output distance in kilometers
        ] 

        fn = [f.name for f in arcpy.ListFields(output_fc_mem)]
        for (in_name, out_name, expr) in remap_cols:
            # create a new field for storing the coord
            arcpy.AddField_management(output_fc_mem, out_name, "DOUBLE")
            # copy the field over from the original
            arcpy.CalculateField_management(output_fc_mem, out_name, expr, "PYTHON_9.3")
            # delete the original field
            if in_name in fn:
                arcpy.DeleteField_management(output_fc_mem, in_name)

        # can't delete length; part of the data model which is 
        # unfortunate -- it's degrees, and has no linear distance.
        # arcpy.DeleteField_management(output_fc_mem, "Shape_Length")

        # copy the final result back to disk.
        if output_fc_mem != output_fc:
            utils.msg("Writing results to disk…")
            arcpy.CopyFeatures_management(output_fc_mem, output_fc)

        utils.msg("Created shortest distance paths successfully: {0}".format(output_fc))
    except Exception as e:
        utils.msg("Error creating geodesic lines.", mtype='error', exception=e)
        sys.exit()

    # clean up: remove intermediate steps. 
    try:
        for layer in [near_table, output_fc_mem]:
            arcpy.Delete_management(layer)
    except Exception as e:
        utils.msg("Unable to delete temporary layer", mtype='error', exception=e)
        sys.exit()

# when executing as a standalone script get parameters from sys
if __name__=='__main__':

    # Defaults when no configuration is provided
    # TODO: change these to be test-based.
    defaults_tuple = (
        ('input_fc', ""),
        ('output_fc', "TestFC"),
    )

    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(mode='script', **defaults)
