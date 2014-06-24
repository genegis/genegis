# ExportToAIS.py: export data to the Alleles in Space (AIS) format
# -*- coding: utf-8 -*-
# Created by: Shaun Walbridge
#             Esri

# Created on: 5 June 2013
# Export data to the Alleles in Space format.

import arcpy
import sys
import time
from datetime import datetime

# local imports
import utils
import config
settings = config.settings()

def main(input_features=None, id_field=None, where_clause=None, output_coords=None, 
        output_genetics=None, mode=settings.mode):
   
    # get the spatial reference of our input, determine the type
    desc = arcpy.Describe(input_features)
    sr = desc.spatialReference
    if sr.type not in ['Geographic', 'Projected']:
        utils.msg("This tools only works with geographic or projected data.", mtype='error')
        sys.exit()

    if not id_field:
        id_field = settings.id_field

    # Find our Loci columns. 
    loci = utils.Loci(input_features)
    utils.msg("loci set: {0}".format(",".join(loci.names)))

    comments = """Export to Alleles in Space from the input `{input_features}`. 
Export occurred on {datetime}
Coordinates are in {sr_name}, a {sr_type} coordinate system.""".format(
        input_features=input_features, datetime=datetime.now(), \
        sr_name=sr.name, sr_type=sr.type.lower())

    if sr.type == 'Geographic':
        # geographic data expected to be (lat, lon)
        loc_a = settings.y_coord
        loc_b = settings.x_coord
    else:
        # two coordinates in a projected space
        loc_a = settings.x_coord
        loc_b = settings.y_coord
   
    selected_columns = [id_field, loc_a, loc_b] + loci.columns
    rows = arcpy.da.SearchCursor(input_features, selected_columns, where_clause)

    coordinate_rows = []
    genetic_rows = []
    for row in rows:
        id_field = row[0]
        loc_a_val = row[1]
        loc_b_val = row[2]
    
        coordinate_row = [id_field, loc_a_val, loc_b_val]
        genetic_row = [id_field]

        for (key, cols) in loci.fields.items():
            # loci values should be separated by an '\'.

            loci_values = []
            for col in cols:
                col_pos = selected_columns.index(col)
                allele_val = row[col_pos]
                # handle missing and incomplete genotypes.
                if allele_val is None:
                    allele_val = "0"
                else:
                    allele_val = str(allele_val)
                loci_values.append(allele_val)

            genetic_row.append('\\'.join(loci_values))

        coordinate_rows.append(coordinate_row)
        genetic_rows.append(genetic_row)

    try:
        # copy the final result back to disk.
        utils.msg("Writing results to disk...")

        # Alleles in Space expects comma-delimited outputs
        sep = ","

        with open(output_coords, 'wb') as coords_file:
            for raw_row in coordinate_rows:
                # convert all data to strings
                row = [utils.xstr(s) for s in raw_row]
                coords_file.write("{0}\n".format(sep.join(row)))
            coords_file.write(";\n")
            coords_file.write(comments)
            utils.msg("Exported coordinates saved to %s." % output_coords)

        with open(output_genetics, 'wb') as genetics_file:
            # start the file with the number or loci
            genetics_file.write("{0}\n".format(loci.count))
            for raw_row in genetic_rows:
                # convert all data to strings
                row = [utils.xstr(s) for s in raw_row]
                genetics_file.write("{0}\n".format(sep.join(row)))
            genetics_file.write(";\n")
            genetics_file.write(comments) 
            utils.msg("Exported genetics saved to %s." % output_genetics)

    except Exception as e:
        utils.msg("Error creating output file.", mtype='error', exception=e)
        sys.exit()

    if mode == 'toolbox':
        time.sleep(4)

# when executing as a standalone script get parameters from sys
if __name__=='__main__':
    # Defaults when no configuration is provided
    # TODO: change these to be test-based.
    defaults_tuple = (
        ('input_features', "C:\\geneGIS\\test.gdb\\test_Spatial"),
        ('id_field',  "Individual_ID"),
        ('where_clause', ""),
        ('output_coords', ''),
        ('output_genetics', '')
    )
 
    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(mode='script', **defaults)
