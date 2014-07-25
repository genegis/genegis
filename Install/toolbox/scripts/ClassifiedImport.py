# ---------------------------------------------------------------------------
# ClassifiedImport.py
#
# Created by: Dori Dick
#             College of Earth, Ocean and Atmospheric Sciences
#             Oregon State Univeristy
#
# Description: This script converts spatially reference genetic data from a
# simple flat file format to a Feature Class viewable in ArcGIS 10.
#
# Required Inputs: Spatially referenced genetic data formatted according to
# the SRGD.csv file format. This data can be for indentifed individuals or
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
import numpy
import os
import sys

# local imports
import utils
import config

"""
Enable local imports; redirect config calls to general config

NOTE: tried to do this with it separated into a script 'add_install_path.py'
      which works fine from a command-line context but doesn't fire from
      ArcGIS interactively. This is likely related to the path-scanning it does
      when trying to export to an .sd / arcgis server endpoint.
"""
def add_install_path():
    local_path = os.path.dirname(__file__)
    add_paths = [
            os.path.join(local_path, '..', '..'), # Install
            os.path.join(local_path, '..',), # Install/toolbox
            os.path.join(local_path, '..', 'lib'), # Install/toolbox/lib
            local_path # Install/toolbox/scripts
    ]
    for path in add_paths:
        full_path = os.path.abspath(path)
        sys.path.insert(0, full_path)

add_install_path()
settings = config.settings()

def main(input_table=None, sr=None, output_loc=None,
    output_gdb=None, output_fc=None, genetic=None,
    identification=None, location=None, other=None,
    mode='toolbox', protected_map=config.protected_columns):

    # set mode based on how script is called.
    settings.mode = mode

    # First, create a geodatabase for all our future results.
    # TODO: can we generate this from a single value?
    gdb_path = os.path.abspath(os.path.join(output_loc, output_gdb + '.gdb'))

    # if the user is calling this from the command-line, they won't have necessarily
    # entered a full path for the FC output. Infer it from the input instead.
    if output_fc.lower().find('gdb') == -1:
        output_fc =  os.path.join(gdb_path, output_fc)

    # check if we received a value spatial reference -- if not, use WGS84.
    if sr in ('', None):
        # default spatial reference can be redefined.
        sr = config.sr

    try:
        # only try to create this GDB if it doesn't already exist.
        if not os.path.exists(gdb_path):
            # Process: Create File GDB
            # SYNTAX: CreateFileGDB_management (out_folder_path, out_name, {out_version})
            arcpy.CreateFileGDB_management(output_loc, output_gdb, "CURRENT")
            utils.msg("File geodatabase successfully created: %s" % gdb_path)
        else:
            utils.msg("File geodatabase already exists, skipping creation.")
    except Exception as e:
        utils.msg("Error creating file geodatabase", mtype='error', exception=e)
        sys.exit()

    # TODO: WE NEED TO DO A FULL CLASSIFICATION OF THE INPUT AND MANUALLY BUILD UP THE LAYER...
    # We'll have two columns per locus, need to import correctly

    # Start things off by importing the table directly. We still need to edit the header
    # because of ArcGIS' restrictions on table names.

    # do we have a text-based file?
    file_type = utils.file_type(input_table)
    if file_type == 'Text':
        # Generate a temporary copy of the input CSV which corrects it for
        # ArcGIS, stripping invalid column label characters.
        data_table = utils.validate_table(input_table)

        # TODO: use field mapping to handle the date-time field?
        utils.protect_columns(data_table, protected_map)
    else:
        data_table = input_table

    # write out our table, after additional validation.
    try:
        arcpy.env.overwriteOutput = settings.overwrite

        # generate table name based on input name
        (label, ext) = os.path.splitext(os.path.basename(input_table))

        # Validate label will produce a valid table name from our input file
        validated_label = arcpy.ValidateTableName(label)

        # write out our filtered table to ArcGIS
        arcpy.TableToTable_conversion(data_table, gdb_path, validated_label)

        if file_type == 'Text':
            # Delete the temporary table with validated names;
            # temp file is stored in the same spot as the original.
            temp_dir = os.path.dirname(input_table)
            temp_path = os.path.join(temp_dir, data_table)
            os.remove(temp_path)

    except Exception as e:
        utils.msg("Error converting table %s to GDB" % input_table, mtype='error', exception=e)
        sys.exit()

    input_csv = os.path.join(gdb_path, validated_label)
    utils.msg("Table successfully imported: \n %s" % input_csv)
    fields = [f.name.lower() for f in arcpy.ListFields(input_csv)]

    # intially, our date column is imported as text to prevent ArcGIS
    # from inadvertently munging it. Add a formatted date column.
    try:
        # TODO: make date field defined elsewhere.
        input_time_field = "Date_Time"
        field_name = 'Date_formatted'
        expression = 'formatDate(!{input_time_field}!)'.format(
            input_time_field=input_time_field)
        code_block = """
import dateutil.parser
def formatDate(input_date):
    parsed_date = dateutil.parser.parse(input_date)
    return parsed_date.strftime("%m/%d/%Y %H:%M:%S")"""
        # check if a formatted date field exists; if so skip this step
        if field_name.lower() not in fields:
            arcpy.AddField_management(input_csv, field_name, 'DATE')
            arcpy.CalculateField_management(input_csv, field_name, expression, "PYTHON_9.3", code_block)
            utils.msg("Added a formatted date field: {field_name}.".format(field_name=field_name))
    except Exception as e:
        utils.msg("Error parsing date information", mtype='error', exception=e)
        sys.exit()

    # coordinate columns
    x = y = None

    # Convert the table to a temporary spatial feature
    try:
        if location is None:
            raise Exception("Required location columns not set.")

        # A temporary XY Layer needed to create the feature class.
        # NOTE: This table is deleted when the script finishes
        temporary_layer = input_csv + '_xy_temp'

        # 'location', ArcGIS passes semicolon separated values
        loc_parts = location.split(";")

        # TODO: ArcGIS doesn't preserve order; do we need separate fields for these? or some other approach?
        if loc_parts[0].lower() in ['x', 'longitude', 'lon']:
            (x, y) = loc_parts[:2]
        else:
            (y, x) = loc_parts[:2]

        # Process: Make XY Event Layer.  This layer is temporary and will be
        # deleted upon script completion.
        # SYNTAX: arcpy.MakeXYEventLayer_management(table, in_x_field,
        #           in_y_field, out_layer, {spatial_reference}, {in_z_field})
        arcpy.MakeXYEventLayer_management(input_csv, x, y, temporary_layer, sr)
    except Exception as e:
        utils.msg("Error making XY Event Layer", mtype='error', exception=e)
        sys.exit()

    utils.msg("XY event layer successfully created.")


    # Copy our features to a permanent layer
    try:
        # for this step, overwrite any existing results
        arcpy.env.overwriteOutput = True

        # Process: Copy Features
        # SYNTAX: CopyFeatures_management (in_features, out_feature_class, {config_keyword}, {spatial_grid_1}, {spatial_grid_2}, {spatial_grid_3})
        arcpy.CopyFeatures_management(temporary_layer, output_fc, "", "0", "0", "0")
        utils.msg("Features succesfully created: \n %s" % output_fc)

    except Exception as e:
        utils.msg("Error copying features to a feature class", mtype='error', exception=e)
        sys.exit()

    utils.msg("Feature Class successfully created, your SRGD file has been imported!")

    try:
        haplotype_table = os.path.join(gdb_path, "{}_{}".format(validated_label, 'Haplotypes'))

        # look up our haplotype data
        haplotypes = utils.Haplotype(output_fc)
        
        # create a dictionary for inserting records
        dts = {'names': ('code', 'haplotype', 'count'),
                       'formats': (numpy.uint16, 'S6', numpy.uint8)}

        # create a numpy formatted structure from this data
        array = numpy.rec.fromrecords(haplotypes.indexed, dtype=dts)

        # output the new table
        arcpy.da.NumPyArrayToTable(array, haplotype_table)
        
        utils.msg("Haplotype table created: \n {}".format(haplotype_table))

    except Exception as e:
        utils.msg("Error creating supplemental haplotype table", mtype='error', exception=e)
        sys.exit()



    # Because we can't pass around objects between this process and the calling
    # addin environment, dump out the settings to our shared configuration file.
    try:
        config.update('fc_path', output_fc.strip())
        config.update('x_coord', x)
        config.update('y_coord', y)

        var_types = {
                'identification': identification,
                'genetic': genetic,
                'location': location,
                'other': other
        }

        if identification is None:
            raise Exception("Required Identification columns not entered.")

        # the first ID field should be used as the default key.
        id_cols = identification.split(";")
        id_field = id_cols[0]
        for (i, col) in enumerate(id_cols):
            # FIXME this will always set individual_id to the primary key.
            if col.lower() == 'individual_id':
                id_field = id_cols[i]
        config.update('id_field', id_field)

        for (var, val) in var_types.items():
            if val is None:
                val = ''
            config.update('%s_columns' % var, val.strip())

    except Exception as e:
        msg = "Error creating output configuration file: %s" % config.config_path
        utils.msg(msg, mtype='error', exception=e)
        sys.exit()

    # clean up: remove intermediate steps.
    try:
        arcpy.Delete_management(temporary_layer)
    except Exception as e:
        utils.msg("Unable to delete temporary layer", mtype='error', exception=e)
        sys.exit()

# when executing as a standalone script get parameters from sys
if __name__=='__main__':

    # Defaults when no configuration is provided
    defaults_tuple = (
        ('input_table', os.path.join(settings.data_dir, "SRGD_example.csv")),
        ('sr', config.sr.exportToString()),
        ('output_loc', os.path.abspath(os.path.dirname(__file__))),
        ('output_gdb', "example_import"),
        ('output_fc', "TestFC"),
        ('genetic', None),
        ('identification', "Individual_ID;Sample_ID"),
        ('location', "Latitude;Longitude"),
        ('other', None)
    )
    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(mode='script', **defaults)
