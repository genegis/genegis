'''
Created by:
Dori Dick
College of Earth, Ocean and Atmospheric Sciences
Oregon State Univeristy

Created on: 29 July 2012
Last modified: 15 May 2013

Description:
This script exports a feature class containing spatially referenced genetic into the text file
format required by Genepop. See http://genepop.curtin.edu.au/ for more information on Genepop.

Required Inputs:
An existing Feature Class containing spatially referenced genetic data (i.e. co-dominant microsatellite data).
An Attribute Field within the Feature Class that can be used to designate different populations.
An Output File Location  and file name for the text file

Optional Inputs:
A Where Clause to identify only those rows with genetic data in the Feature Class.  Uses a SQL Expression.
NOTE: This parameter is optional and was included because some data sets may have individual IDs based
on more than just genetics (i.e. photo-id).

Script Outputs:
A text file formatted to meet the required input file format for Genepop.

This script was developed to work with ArcGIS 10.1 and Python 2.7 installed during ArcGIS installation.
'''

import arcpy
import re
import sys
import time
from collections import OrderedDict
from datetime import datetime

# local imports
import utils
import config
settings = config.settings()

def normalize(allele):
    val = str(allele)
    if allele == '' or allele is None or int(allele) == 0:
        val = "000"
    return val

def main(input_features=None, id_field=None, where_clause=None, order_by=None, 
        output_name=None, mode=settings.mode):

    utils.msg("Executing ExportToGenepop.")

    # try to set the id based on input, otherwise go off of the config.
    if id_field is not None:
        primary_id = id_field
    else:
        primary_id = settings.id_field

    # Create and open the Output text file to which the data will be written
    with open(output_name, "w") as output_file:
        utils.msg("Opened `%s` for writing." % output_name)

        # Find our Loci columns. 
        loci = utils.Loci(input_features)
        utils.msg("Loci set: {0}".format(",".join(loci.names)))

        # pull out Haplotype information
        haplotypes = utils.Haplotype(input_features)
      
        # we have haplotype data, include it
        if haplotypes.defined:
            # map haplotypes to a two digit number with leading zero
            haplo_formatted = [(h[1], "{0:03d}".format(h[0])) for h in haplotypes.indexed]
            haplo_formatted_label = [" to ".join(h) for h in haplo_formatted] 
            utils.msg("Haplotype mappings used: {0}".format(
                    ", ".join(haplo_formatted_label)))
            haplo_lookup = dict(haplo_formatted)
            # if no haplotype is found, leave an empty value
            haplo_lookup[None] = '000'

        # sql clause can be prefix or suffix; set up ORDER BY
        sql_clause = (None, "ORDER BY {0} ASC".format(order_by))

        # query the input_features in ascending order; filtering as needed
        selected_columns = [settings.id_field, order_by] + loci.columns
        if haplotypes.defined:
            selected_columns += [haplotypes.column]

        rows = arcpy.da.SearchCursor(input_features, selected_columns, 
                where_clause, "", "", sql_clause)
        current_group = ""

        for (i, row) in enumerate(rows):
            id_field = row[0] # as set on import
            group = row[1] # second column is 'order_by', or key column
            label = "{0}-{1},".format(id_field, group).replace(" ", "_")
            
            if i == 0:
                # Create the Genepop header information required for the text file.
                comment_line = "geneGIS: Export to Genepop from the feature class " + \
                        "`{input_features}`.".format(input_features=input_features) + \
                        " Export occurred on {datetime}.\n".format(datetime=datetime.now())
                utils.msg("Comment: %s" % comment_line)

                # write header row
                header = comment_line
                header += "{0}{1}".format(" " * len(label), ",".join(loci.names))
                if haplotypes.defined:
                    header += ",{0}".format(haplotypes.column)
                header += '\n'
                output_file.write(header)

            if group != current_group:
                output_file.write("Pop\n")
                current_group = group

            result_row = [label]

            # GENEPOP only supports haploid and diploid data.
            for (key, cols) in loci.fields.items():
                loci_val = ""
                for col in cols:
                    col_pos = selected_columns.index(col)
                    loci_val += normalize(row[col_pos])
                result_row.append(loci_val)
            if haplotypes.defined:
                haplo = row[-1]
                result_row.append(haplo_lookup[haplo])
            output_file.write(" ".join(result_row) + "\n")

    utils.msg("Exported results saved to %s." % output_name)

    if mode == 'toolbox':
        time.sleep(4)

if __name__ == '__main__':
    # Defaults when no configuration is provided
    # TODO: change these to be test-based.
    defaults_tuple = (
        ('input_features', 
        "C:\\geneGIS\\WorkingFolder\\test_20March.gdb\\SPLASH_Whales"),
        ('id_field', 'Individual_ID'),
        ('where_clause', "'Individual_ID' <> ''"),
        ('order_by', 'Region'),
        ('output_name',  "C:\\geneGIS\\WorkingFolder\\Genepop_Export.txt")
    )

    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(mode='script', **defaults)
