# ---------------------------------------------------------------------------
# ExportGenAlEx.py
#
# Created by: Dori Dick
#             College of Earth, Ocean and Atmospheric Sciences
#             Oregon State Univeristy
#
# Created on: 19 March 2012
#  
# Description: This script exports a feature class containing spatially 
#              referenced genetic into the text file format required by 
#              GenAlEx (Peakall and Smouse 2006), an MS Excel Add-In created
#              to run various genetic analyses in Excel.  GenAlEx is 
#              available at: http://www.anu.edu.au/BoZo/GenAlEx/
#
# Required Inputs: An existing Feature Class containing spatially referenced 
#                  genetic data for additional analysis in GenAlEx.
#
# Optional Inputs: A Where Clause option using a SQL Expression to identify 
#                  only those rows with genetic data in the Feature Class.  
#
#            NOTE: This parameter is optional and was included because some 
#                  data sets may have individual IDs based on more than just
#                  genetics (i.e. photo-id).  
#
#                  An Attribute Field that distinguishes the populations in
#                  the Input Feature Class.

#            NOTE: This parameter is optional and was included because
#                  some data sets may have more than one population in it.  
#
# Script Outputs:  A delimited text file formatted to match the required 
#                  input for GenAlEx.
#              
# This script was developed and tested on ArcGIS 10.1 and Python 2.7.
#
# --------------------------------------------------------------------------

import arcpy
import copy
import csv
import os
import re
import sys
import time
from collections import OrderedDict

# local imports
import utils
import config

settings = config.settings()

def main(input_features=None, id_field=None, where_clause='', order_by=None,
        output_name=None, format_type='Excel', mode='toolbox'):

    # try to set the id based on input, otherwise go off of the config.
    if id_field is not None:
        primary_id = id_field
    else:
        primary_id = settings.id_field

    # set mode based on how script is called.
    settings.mode = mode
    add_output = arcpy.env.addOutputsToMap
    arcpy.env.addOutputsToMap = True

    # ensure our order by field exists
    fields = [f.name for f in arcpy.ListFields(input_features)]
    if not order_by in fields:
        utils.msg("Unable to find order_by field, `{}`".format(order_by))
        sys.exit()

    # The Input Feature Class
    # == input_features

    # Where clause that can be used to pull out only those rows with genetic
    # data from the feature class.

    # NOTE: This parameter is optional and was included because some data
    # sets may have individual IDs based on more than just genetics
    # (i.e. photo-id).  If your data only has genetic records, this
    # parameter can be left blank.
    # == where_clause

    # The Attribute Field that distinguishes the populations in the input.

    # NOTE: This parameter is optional and was included because some data
    # sets may have more than one population in it.
    # == order_by

    try:
        # test opening the file to which the data will be written
        output_file = open(output_name, "wb")
    except Exception as e:
        utils.msg("Unable to open output file", mtype='error', exception=e)
        sys.exit()

    # initialize our haplotypes data
    haplotypes = utils.Haplotype(input_features)

    # set up the environment depending on the output format
    if format_type == 'Excel':
        # xlwt will write directly; only opened to make sure we can write to the location
        output_file.close()
        try:
            import xlwt
        except ImportError as e:
            msg = "Writing Excel Spreadsheets requires the `xlwt` library, which is" + \
                    " included in ArcGIS 10.2+. If you'd like Excel support in " + \
                    " ArcGIS 10.1, please install `xlwt` manually from PyPI: " +  \
                    "   https://pypi.python.org/pypi/xlwt/0.7.3."
            utils.msg(msg, mtype='error', exception=e)
            sys.exit() 

        # only replace Nones, keep numeric types
        from utils import xrep as xstr
        from utils import zrep as zstr
    else:
        # convert all strings to text
        from utils import zstr as zstr
        from utils import xstr as xstr

    # list of lists to emulate the Excel sheet
    output_rows = []
    haplotype_rows = []

    utils.msg("Output file open and ready for data input")

    # Find our Loci columns. 
    loci = utils.Loci(input_features)
    utils.msg("loci set: {0}".format(",".join(loci.names)))

    """
    header row contains (in order):
     - number of loci
     - number of samples
     - number of populations
     - size of pop 1
     - size of pop 2
     - ...

    second row contains:
     - three blank cells
     - loci 1 label
     - loci 2 label
     - ...

    DATA starts at C4. See "GenAlEx Guide.pdf" page 15.
    """

    # sql clause can be prefix or suffix; set up ORDER BY
    sql_clause = (None, "ORDER BY {0} ASC".format(order_by))
    # query the input_features in ascending order; filtering as needed
    selected_columns = order_by
    pops = OrderedDict()
    rows = arcpy.da.SearchCursor(input_features, selected_columns,
            where_clause, "", "", sql_clause)
    row_count = 0
    for row in rows:
        row_count += 1
        pop = row[0]
        if pops.has_key(pop):
            pops[pop] +=1
        else:
            pops[pop] = 1

    pop_counts = [xstr(p) for p in pops.values()]
   
    # Creating the GenAlEx header information required for the text file.
    output_rows += [[loci.count, row_count, len(pops.keys())] + pop_counts]

    # optional title, then a list of each population
    output_rows += [['', '', ''] + pops.keys()]

    # first two rows almost exactly the same
    haplotype_rows = copy.deepcopy(output_rows)
    # 'number of loci' should be 1 for haplotype-only data
    haplotype_rows[0][0] = 1

    loci_labels = []
    for (key, cols) in loci.fields.items():
        loci_labels += [key] + [''] * (len(cols) - 1)

    # get the spatial reference of our input, determine the type
    desc = arcpy.Describe(input_features)
    sr = desc.spatialReference
    if sr.type == 'Projected':
        loc_a = settings.x_coord
        loc_b = settings.y_coord
    if sr.type == 'Geographic':
        # geographic data expected to be (lat, lon)
        loc_a = settings.y_coord
        loc_b = settings.x_coord

    primary_columns = [primary_id, order_by, loc_a, loc_b]
    exclude = primary_columns + loci.columns + ['OBJECTID', 'Shape']
    unselected_columns = []
    for field in fields:
        # add any field not currently mapped
        if field not in exclude:
            unselected_columns.append(field)
    # extra fields should start with an empty line, the location, then any
    # columns not otherwise mapped.
    extra_columns = ['', loc_a, loc_b] + unselected_columns

    output_rows += [[primary_id, order_by] + loci_labels + extra_columns]
    if haplotypes.defined:
        haplotype_rows += [[primary_id, order_by, haplotypes.column]]
    utils.msg("Header info written to output")

    # Note the WhereClause: Because the SPLASH data has both photo-id and genetic
    # records, but GenAlEx only uses genetic data, the WhereClause is used to ensure
    # only those records with genetic data are copied to the text file.
    selected_columns = primary_columns + unselected_columns + loci.columns

    for row in arcpy.da.SearchCursor(input_features, selected_columns,
            where_clause, "", "", sql_clause):
        id_field = row[0] # as set on import
        pop = row[1] # second column is 'order_by', or key column
        loc_a_val = row[2]
        loc_b_val = row[3]
        unselected_rows = list(row[4:len(unselected_columns)+4])
        result_row = [id_field, pop]
        for (key, cols) in loci.fields.items():
            for col in cols:
                col_pos = selected_columns.index(col)
                result_row.append(row[col_pos])
        result_row = result_row + ["", loc_a_val, loc_b_val] + unselected_rows
        output_rows += [[zstr(s) for s in result_row]]
        if haplotypes.defined:
            row_val = row[selected_columns.index(haplotypes.column)]
            if row_val:
                haplotype_val = haplotypes.lookup[row_val]
            else:
                haplotype_val = 0
            haplotype_res = [id_field, pop, haplotype_val]
            haplotype_rows += [[zstr(s) for s in haplotype_res]]

    # depending on our driver, handle writing dependent on type
    if format_type == 'Excel':
        # initialize our spreadsheet
        workbook = xlwt.Workbook()

        # codominant data
        worksheet_co = workbook.add_sheet('Codominant')
        for (i, row) in enumerate(output_rows):
            for (j, val) in enumerate(row):
                worksheet_co.write(i, j, val)

        # the haplotype data
        if haplotypes.defined:
            worksheet_hap = workbook.add_sheet('Haplotype')
            for (i, row) in enumerate(haplotype_rows):
                for (j, val) in enumerate(row):
                    worksheet_hap.write(i, j, val)

            # write out a mapping of haplotype names
            worksheet_hap_map = workbook.add_sheet('Haplotype Map')
            worksheet_hap_map.write(0, 0, haplotypes.column)
            worksheet_hap_map.write(0, 1, 'Numeric Code')

            for (i, (hap, code)) in enumerate(haplotypes.lookup.items(), start=1):
                worksheet_hap_map.write(i, 0, hap)
                worksheet_hap_map.write(i, 1, code)

        workbook.save(output_name)            
    else:
        # create a CSV writer
        writer = csv.writer(output_file, dialect='excel',
                quotechar='"', quoting=csv.QUOTE_ALL)
        for row in output_rows:
            writer.writerow(row)

    utils.msg("Exported results saved to %s." % output_name)
    # Close Output text file
    output_file.close()

    if mode == 'toolbox':
        time.sleep(4)

    arcpy.env.addOutputsToMap = add_output

if __name__ == '__main__':
    # Defaults when no configuration is provided
    input_features = os.path.join(settings.example_gdb, "SRGD_example_Spatial")
    defaults_tuple = (
        ('input_features', input_features),
        ('id_field', 'Individual_ID'),
        ('where_clause', "'Individual_ID' <> ''"),
        ('order_by', 'Region'),
        ('output_name',  "GenAlEx_Export.xls")
    )
    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(mode='script', **defaults)
