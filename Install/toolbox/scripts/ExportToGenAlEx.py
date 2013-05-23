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
import os
import sys
import collections

def main(input_features=None, where_clause=None, order_by=None, 
        output_name=None):

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
        # Create and open the text file to which the data will be written
        output_file = open(output_name, "w")
    except Exception as e:
        utils.msg("Unable to open text file", mtype='error', exception=e)
    
    utils.msg("Output file open and ready for data input")
            
    try: 
        # TODO: TALK TO SCOTT AND DORI ABOUT HOW THIS WORKS, HOW CLOSELY WE 
        # WANT TO REPLICATE THE GENALEX format?
        # Creating the GenAlEx header information required for the text file. 
        # NOTE: This includes 2 blank rows followed by the data.
        output_file.write("\n")     
        output_file.write("\n")

        # Individual_ID, POPULATIONS, THEN: two columns for each Locus.
        #column_labels = [individual_id, population, locus_1, locus_2, ...]
        # output
        output_file.write("Individual_ID" + "," + order_by + "," + "Locus1_A1" + "," + "" + "," +\
                                 "Locus2_A1" + "," + "" + "," + "Locus3_A1" + "," + "" + "," + "Locus4_A1" + "," + "" + "," +\
                                 "Locus5_A1" + "," + "" + "," + "Locus6_A1" + "," + "" + "," + "Locus7_A1" + "," + "" + "," +\
                                 "Locus8_A1" + "," + "" + "," + "Locus9_A1" + "," + "" + "," + "Locus10_A1" + "," + "" + "," +\
                                 "Locus11_A1" + "," + "" + "," + "Locus12_A1" + "," + "" + "," + "Locus13_A1" + "," + "" + "," +\
                                 "Locus14_A1" + "," + "" +"," + "" + "," + "Latitude" + "," + "Longitude" + "\n") 
        
    except:
        print "Unable to write header info to text file"
        
    print "Header info written to text file"

    try:
        
        # Creating a search cursor that will move through the input feature class, row by row
        # Note the WhereClause: Because the SPLASH data has both photo-id and genetic records, but GenAlEx only uses genetic data, the 
        #                       WhereClause is used to ensure only those records with genetic data are copied to the text file. 
        rows = arcpy.SearchCursor(input_features)
        rows = arcpy.SearchCursor(input_features, where_clause, "", "", order_by + " A")
        row = rows.next()
        
        # A while loop used to move through each row of data and pull the value for each of the necessary fields
        while row:     
            OutputFile.write(str(row.Individual_ID) + "," + str(row.getValue(order_by))+ "," + str(row.Locus1_A1) + "," + str(row.Locus1_A2) + "," +\
                             str(row.Locus2_A1) + "," + str(row.Locus2_A2) + "," + str(row.Locus3_A1) + "," + str(row.Locus3_A2) + "," + str(row.Locus4_A1) + "," + str(row.Locus4_A2) + "," +\
                             str(row.Locus5_A1) + "," + str(row.Locus5_A2) + "," + str(row.Locus6_A1) + "," + str(row.Locus6_A2) + "," + str(row.Locus7_A1) + "," + str(row.Locus7_A2) + "," +\
                             str(row.Locus8_A1) + "," + str(row.Locus8_A2) + "," + str(row.Locus9_A1) + "," + str(row.Locus9_A2) + "," + str(row.Locus10_A1) + "," + str(row.Locus10_A2) + "," +\
                             str(row.Locus11_A1) + "," + str(row.Locus11_A2) + "," + str(row.Locus12_A1) + "," + str(row.Locus12_A2) + "," + str(row.Locus13_A1) + "," + str(row.Locus13_A2) + "," +\
                             str(row.Locus14_A1) + "," + str(row.Locus14_A2) + "," + "" + "," + str(row.Latitude) + "," + str(row.Longitude) + "\n")
            row = rows.next()

    except:
        print "Unable to write data to text file"

    print "Data written to text file"

    # Close Output text file
    OutputFile.close()

    print "Done!"
if __name__ == 'main':
    # Defaults when no configuration is provided
    # TODO: change these to be test-based.
    defaults_tuple = (
        ('input_features', 
        "C:\\geneGIS\\WorkingFolder\\test_20March.gdb\\SPLASH_Whales"),
        ('where_clause', "Individual_ID" + "<>'" + str("")+"'"),
        ('order_by', 'Area'),
        ('output_location',  "C:\\geneGIS\\WorkingFolder\\GenAlEx_Codominant_Export")
    )

    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(*defaults.values(), mode='script')
