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

NOTE:  Keep a record of the Loci names and their order as this script uses generic locus names 
(e.g., Locus1_A1, Locus1_A2, Locus2_A1, Locus2_A2 etc.)

This script was developed to work with ArcGIS 10.1 and Python 2.7 installed during ArcGIS installation. 
''' 

import arcpy
import os
import sys
import binascii
import collections
from datetime import datetime

# local imports
import utils
import config

def main(input_features=None, where_clause=None, order_by=None,  output_name=None, 
         mode=config.mode):
        
        utils.msg("Executing ExportToGenepop.")   
        
        # Create and open the Output text file to which the data will be written
        with open(output_name + ".txt", "w") as output_file:
            utils.msg("file open for writing")
            
            # Create the Genepop header information required for the text file. 
            # NOTE: Line 1 includes user inputed information about the data in the file.  Lines 2-15 list the generic Loci names
            #FIXME: What we want is to have the script write out the acutal Loci names of the input file.  This way it will be specific to the user and will not be 
            #fixed in naming convention or the number of loci 
            output_file.write("Export to Genepop from the feature class: " + input_features + ". Export occurred on: " + str(datetime.now()) + "\n")  
            output_file.write("Locus1\n")
            output_file.write("Locus2\n")
            output_file.write("Locus3\n")
            output_file.write("Locus4\n")
            output_file.write("Locus5\n")
            output_file.write("Locus6\n")
            output_file.write("Locus7\n")
            output_file.write("Locus8\n")
            output_file.write("Locus9\n")
            output_file.write("Locus10\n")
            output_file.write("Locus11\n")
            output_file.write("Locus12\n")
            output_file.write("Locus13\n")
            output_file.write("Locus14\n")  
            
            # Creating a search cursor that will move through the Input Feature Class row by row (Parameter1),
            # specifying only genetic records (Parameter2, if specified by the used) and ordering the data by a population 
            # field (Parameter3) in ascending order
            rows = arcpy.SearchCursor(input_features, where_clause, "", "", order_by + " A")
        
            # Defining an empty variable as AreaName 
            AreaName = ""
          
            # Creating a list of the generic Loci names 
            LocusNames = ["Locus1_A1", "Locus1_A2", "Locus2_A1", "Locus2_A2", "Locus3_A1", "Locus3_A2", "Locus4_A1",\
                    "Locus4_A2", "Locus5_A1", "Locus5_A2", "Locus6_A1", "Locus6_A2", "Locus7_A1", "Locus7_A2", "Locus8_A1", \
                    "Locus8_A2", "Locus9_A1", "Locus9_A2", "Locus10_A1", "Locus10_A2", "Locus11_A1", "Locus11_A2", \
                    "Locus12_A1", "Locus12_A2", "Locus13_A1", "Locus13_A2", "Locus14_A1", "Locus14_A2"] 
            
            # For loop used to move through each row of data and pull the user defined Parameter4 value for each of the necessary fields
            for row in rows:
                    # Defining a variable for the Parameter3 value
                    temp = str(row.getValue(order_by))
                    # Set a boolean statement 
                    HaveZero = False                   
            
            # If temp is not equal to the AreaName
            if temp <> AreaName:
                    # Write "Pop" to the output text file and go to new line
                    output_file.write("Pop" + "\n")
                    # Re-define AreaName = temp
                    AreaName = temp 
            # Set a boolean statement
            OddName = False
            # Write to the text file the IndividualID-Parameter3 Value
            output_name.write(str(row.Individual_ID) + "-" + str(row.getValue(order_by)) +"," + " ")
           
           # For loop used to move through the LocusNames list
            for Name in LocusNames:
                    # Defining a variable for the LocusValue
                    LocusValue = str(row.getValue(Name))
                    # If the LocusValue is equivalent to a 0 or a 00
                    if LocusValue == "0" or LocusValue == "00":
                            # then HaveZero is True
                            HaveZero = True 
                            # Make the LocusValue 000
                            LocusValue = str("000")                      
                    
            # Write to the output text file the LocusValue            
            output_name.write(LocusValue)
            
            # If OddName is equivalent to True
            if OddName == True:
                    # Write to the output text file a space
                    output_name.write(" ")

                    # Update flag - if OddName is equivalent to False 
                    if OddName == False:
                            # Set OddName to true
                            OddName = True
                    
            else:
                    # Re-setting OddName to False
                    OddName = False
             
            # Write to output text file a new line
            output_name.write("\n")
        
            # Go to the next row    
            row += 1
