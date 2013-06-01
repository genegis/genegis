# ExportToSpagedi.py: export our data to the SPAGeDi format
# -*- coding: utf-8 -*-
# Created by: Shaun Walbridge
#             Esri

# Created on: 31 May 2013
# Export data to SPAGeDi format.

import arcpy
import os
import re
import sys
import time
from collections import OrderedDict
from datetime import datetime

# local imports
import utils
import config

def main(input_features=None, where_clause=None, order_by=None, 
        output_name=None, mode=config.settings.mode):
   
    # get the spatial reference of our input, determine the type
    desc = arcpy.Describe(input_features)
    sr = desc.spatialReference
    if sr.type not in ['Geographic', 'Projected']:
        utils.msg("This tools only works with geographic or projected data.", mtype='error')
        sys.exit()
   
    # Find our Loci columns. 
    loci = OrderedDict() 
    loci_columns = []
    genetic_columns = config.settings.genetic_columns.split(";")
    loci_expr = '^l_(.*)_[0-9]+'
    for field in [f.name for f in arcpy.ListFields(input_features)]:
        match = re.match(loci_expr, field, re.IGNORECASE)
        if match:
            name = match.groups()[0]
            if loci.has_key(name):
                loci[name].append(field)
            else:
                loci[name] = [field] 
            loci_columns.append(field)

    utils.msg("loci set: {0}".format(",".join(loci.keys())))

    # sql clause can be prefix or suffix; set up ORDER BY
    sql_clause = (None, "ORDER BY {0} ASC".format(order_by))
    pops = OrderedDict()
    # query the input_features in ascending order; filtering as needed
    rows = arcpy.da.SearchCursor(input_features, order_by, where_clause, "", "", sql_clause)
    row_count = 0
    for row in rows:
        row_count += 1
        pop = row[0]
        if pops.has_key(pop):
            pops[pop] +=1
        else:
            pops[pop] = 1

    # Start with any number of header lines describing what this 
    # file is, each line should be prefixed with //. 
    comments = """// Export to SPAGeDi from the input `{input_features}`. 
// Export occurred on {datetime}
// Coordinates are in {sr_name}, a {sr_type} coordinate system.""".format(
        input_features=input_features, datetime=datetime.now(), \
        sr_name=sr.name, sr_type=sr.type)

    comment_row = [comments]

    """ 
    There are three possible ways to specify population (SPAGeDi manual, 2.4):
    
    1) as categorical groups, where one population includes all individuals 
       sharing the same categorical variable.

    2) as spatial groups, where a spatial group includes all individuals 
       sharing the same spatial coordinates and following each other in 
       the data file.

    3) as spatio-categorical groups, where a spatio-categorical group 
       includes all individuals belonging to both the same spatial 
       group and categorical group. When populations are defined using the 
       categorical variable, the spatial coordinates of a given population 
       are computed by averaging the coordinates of the individuals it contains.
    """

    # FIXME: another spot where 'observation_id' differs from 'individual_id';
    # deduplicate in order to have one value PER individual PER population.

    categories = len(pops.keys())

    # FIXME: presumes only two coords, SPAGeDi supports three. Extract depth?
    if sr.type == 'Geographic':
        # Assumes decimal degrees; based on the statement 'if the number of 
        # spatial coordinates is set to -2, latitudes and longitudes must be 
        # given in degrees with decimal, using negative numbers for Southern 
        # latitude or Western longitude.
        xy_type = -2
        # geographic data expected to be (lat, lon)
        loc_a = config.settings.y_coord
        loc_b = config.settings.x_coord
    else:
        # two coordinates in a projected space
        xy_type = 2
        loc_a = config.settings.x_coord
        loc_b = config.settings.y_coord
   
    num_loci = len(loci.keys())

    # FIXME: loci number of digits, defined in SPAGeDi manual 3.1 as "number 
    # of digits used to code one allele (1 to 3); or set a value =0 (in fact 
    # the value given for missing data) in the case of dominant markers".
    loci_digits = 2 

    # get the maximum number of different values per loci
    max_ploidy = max(map(len, loci.values()))

    # 1st line: set of 6 numbers separated by a tabulation representing: 
    header_row = [
        row_count,   # number of invidivuals
        categories,  # number of categories
        xy_type,     # number of coordinates
        num_loci,    # number of loci 
        loci_digits, # number of digits used to code one allele
        max_ploidy   # max ploidy in the data
    ]

    # 2nd line: # of distance intervals; upper distance of each interval.

    # note 1: alternatively you can enter only the desired number of intervals
    #         preceded by a negative sign; the program then defines the 
    #         n maximal distances in such a way that the number of pairwise 
    #         comparisons within each distance interval is approx. constant.
    # note 2: if you do not wish distance intervals, put 0
    # note 3: if you use latitude + longitude, distance intervals 
    #         must be given in km.

    # TODO: what is this and how do we use it effectively?
    distances_row = [0]

    # 3rd line: column labels (<=15 characters).
    base_cols = [config.settings.id_field, order_by, loc_a, loc_b] 
    labels_row = base_cols + loci.keys()

    # where_clause is used to ensure only those records with genetic data 
    # are copied to the output.
    selected_columns = base_cols + loci_columns
    rows = arcpy.da.SearchCursor(input_features, selected_columns, \
            where_clause, "", "", sql_clause)

    data_rows = []
    for row in rows:
        # our two string fields can't contain spaces, based on Autocio.c: 3857 
        id_field = row[0].replace(" ", "_")
        pop_field = row[1].replace(" ", "_") # 'order_by', or population 'group by'
        loc_a_val = row[2]
        loc_b_val = row[3]

        data_row = [id_field, pop_field, loc_a_val, loc_b_val]

        for (key, cols) in loci.items():
            # Loci data can be encoded in a number of formats, the values
            # separated by any non-numeric values (SPAGeDi manual, 3.2.1). 
            # Here, we use spaces.

            loci_values = []
            for col in cols:
                col_pos = selected_columns.index(col)
                allele_val = row[col_pos]
                # FIXME: handle missing and incomplete genotypes.
                if allele_val is None:
                    allele_val = "0"
                else:
                    allele_val = str(allele_val)
                loci_len = len(allele_val) 
                if loci_len > loci_digits:
                    loci_digits = loci_len
                loci_values.append(allele_val)

            data_row.append(" ".join(loci_values))
        data_rows.append(data_row)

    # update header based on revised loci_digits
    header_row[4] = loci_digits

    # Now compute the lines between these locations.
    try:
        # copy the final result back to disk.
        utils.msg("Writing results to disk…")

        output_rows = [comment_row, header_row, distances_row, labels_row] + \
                data_rows

        # SPAGeDi expects tab-delimited outputs
        sep = "\t"

        with open(output_name, 'w') as output_file:
            for raw_row in output_rows:
                # convert all data to strings
                row = [str(s) for s in raw_row]
                output_file.write("{0}\n".format(sep.join(row)))

            # after the last line of invidivual data the word END is required.
            output_file.write("END\n")

    except Exception as e:
        utils.msg("Error creating output file.", mtype='error', exception=e)
        sys.exit()

    utils.msg("Exported results saved to %s." % output_name)
    if mode == 'toolbox':
        time.sleep(4)

# when executing as a standalone script get parameters from sys
if __name__=='__main__':
    # Defaults when no configuration is provided
    # TODO: change these to be test-based.
    defaults_tuple = (
        ('input_features', "C:\\geneGIS\\test.gdb\\test_Spatial"),
        ('output_name',  "C:\\geneGIS\\spagedi_export.txt"),
        ('where_clause', ""),
        ('order_by', 'Region')
    )
    
    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(mode='script', **defaults)
