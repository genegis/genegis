# SelectByAttributes.py
# Created by: Dori Dick
#             College of Earth, Ocean and Atmospheric Sciences
#             Oregon State Univeristy
#
# Created on: 20 April 2012
# Last modified: 28 July 2014
#
# Description: This script allows the user to perform up to 3 Select By Attribute
#              selections on an input feature class and then exports the selected
#              records to a new feature class.
#
#              Selections are based on the attribute fields of the feature class
#              and use a SQL expression for the selection criteria. The first
#              selection is required and considered to be a "NEW_SELECTION".
#              The other  two selections are optional.
#
#              There are 3 selection types available to use with this tool:
#                   1. NEW_SELECTION: The resulting selection; replaces any previous
#                                     existing selection
#                   2. ADD_TO_SELECTION: The resulting selection is added to an
#                                        existing selection.  If no selection exists,
#                                        it acts like a NEW_SELECTION.
#                   3. SUBSET_SELECTION: The resulting selection is combined with an
#                                        existing selection; only records common to
#                                        both are retained.
#
# Required Inputs:
#   - An existing Feature Class containing spatially referenced genetic data
#   - A NEW_SELECTION SQL expression
#   - An output feature class location.
#
# Optional Inputs:
#   - A second and third selection type and assicated SQL expressions
#
# Script Outputs:
#   - A feature class.


import arcpy
import os
import sys
# local imports
import utils
import config

settings = config.settings()

def select_by(layer, selection, expression):
    try:
        utils.msg("Performing selection {} with query {}".format(selection, expression))
        arcpy.SelectLayerByAttribute_management(layer, selection, expression)
    except Exception as e:
        utils.msg("Unable to select by attributes", mtype='error', exception=e)
        sys.exit()

def main(input_fc=None, selection_1=None, expression_1=None, selection_2=None,
        expression_2=None, selection_3=None, expression_3=None, output_fc=None,
        mode='toolbox'):

    # set mode based on how script is called.
    settings.mode = mode
    add_output = arcpy.env.addOutputsToMap
    arcpy.env.addOutputsToMap = True

    arcpy.env.overwriteOutput = settings.overwrite

    # get the spatial reference of input
    desc = arcpy.Describe(input_fc)
    sr = desc.spatialReference

    # Perform manipulations on an in-memory copy of the data
    utils.msg("Copying features into memory")
    temp_fc = 'in_memory/select_by_attributes'
    temp_layer = "select_by_attributes_lyr"
    arcpy.CopyFeatures_management(input_fc, temp_fc)
    arcpy.MakeFeatureLayer_management(temp_fc, temp_layer)

    # initial selection
    select_by(temp_layer, selection_1, expression_1)

    if selection_2 and expression_2:
        select_by(temp_layer, selection_2, expression_2)

    if selection_3 and expression_3:
        select_by(temp_layer, selection_3, expression_3)

    utils.msg("Writing results to {}".format(output_fc))
    arcpy.CopyFeatures_management(temp_layer, output_fc)

    # restore add outputs state
    arcpy.env.addOutputsToMap = add_output

# when executing as a standalone script get parameters from sys
if __name__ == '__main__':
    # Defaults when no configuration is provided
    defaults_tuple = (
        ('input_fc', os.path.join(settings.example_gdb, "SRGD_example_Spatial")),
        ('selection_1', 'NEW_SELECTION'),
        ('expression_1', "\"Haplotype\" = 'E1'"),
        ('selection_2', 'SUBSET_SELECTION'),
        ('expression_2', "\"Region\" = 'CA-OR'"),
        ('output_fc', os.path.join(settings.example_gdb, "example_select_by_attrs"))
    )

    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(mode='script', **defaults)
