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

def normalize(allele):
    val = str(allele)
    if allele == '' or int(allele) == 0:
        val = "000"
    return val

def main(input_features=None, where_clause=None, order_by=None,  output_name=None,
         mode=config.settings.mode):

    utils.msg("Executing ExportToGenepop.")

    # Create and open the Output text file to which the data will be written
    with open(output_name, "w") as output_file:
        utils.msg("Opened `%s` for writing." % output_name)

        # Create the Genepop header information required for the text file.
        comment_line = "Export to Genepop from the feature class `{input_features}`. Export occurred on {datetime}.\n".format(input_features=input_features, datetime=datetime.now())
        output_file.write(comment_line)
        utils.msg("comment: %s" % comment_line)

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

        output_file.write("\n".join(loci.keys()) + "\n")
        utils.msg("loci set: {0}".format(",".join(loci.keys())))
        # sql clause can be prefix or suffix; set up ORDER BY
        sql_clause = (None, "ORDER BY {0} ASC".format(order_by))
        # query the input_features in ascending order; filtering as needed
        selected_columns = loci_columns + [config.settings.id_field, order_by]
        rows = arcpy.da.SearchCursor(input_features, selected_columns, where_clause, "", "", sql_clause)
        current_group = ""
        for row in rows:
            group = row[-1] # last column is 'order_by', or key column
            id_field = row[-2] # as set on import
            if group != current_group:
                output_file.write("Pop\n")
                current_group = group

            label = "{0}-{1},".format(id_field, group).replace(" ", "_")
            result_row = [label]

            # GENEPOP only supports haploid and diploid data.
            for (key, cols) in loci.items():
                loci_val = ""
                for col in cols:
                    col_pos = selected_columns.index(col)
                    loci_val += normalize(row[col_pos])
                result_row.append(loci_val)
            output_file.write(" ".join(result_row) + "\n")
    utils.msg("Exported results saved to %s." % output_name)
    time.sleep(4)
