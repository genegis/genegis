# -*- coding: utf-8 -*-

import csv
import os
import sys
import re
import arcpy

# enable local imports; allow importing both this directory and one above
local_path = os.path.dirname(__file__)
for path in [local_path, os.path.join(local_path, '..')]:
    full_path = os.path.abspath(path)
    sys.path.insert(0, os.path.abspath(path))

# addin specific configuration and utility functions
import utils
import config

# import utilities & config from our scripts as well
from scripts import utils

class Toolbox(object):
    def __init__(self):
        self.label = u'geneGIS_Jan_2013'
        self.alias = ''
        self.tools = [ExportGenAlEx, SelectDataByAttributes, ClassifiedImport, extractRasterByPoints]

# Tool implementation code
class ClassifiedImport(object):
    class ToolValidator:
      """Class for validating a tool's parameter values and controlling
      the behavior of the tool's dialog."""
    
      def __init__(self, parameters):
        """Setup arcpy and the list of tool parameters."""
        import arcpy
        self.params = parameters
    
      def initializeParameters(self):
        """Refine the properties of a tool's parameters.  This method is
        called when the tool is opened."""
        return
    
      def updateParameters(self):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parmater
        has been changed."""
        return
    
      def updateMessages(self):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return
    
    def __init__(self):
        self.label = u'Import Data'
        self.description = u'This tool allows the user to covert an input file (a text file or Excel spreadsheet formated with the SRGD specifications) to a feature class within a file geodatabase.'
        self.canRunInBackground = False
        # perform some dynamic list filtering, in the case that we have a 
        # table input selected.
        self.cols = {
            'input_csv': 0,
            'sr': 1,
            'output_loc': 2,
            'output_gdb': 3,
            'output_fc': 4,
            'Genetic': 5,
            'Identification': 6,
            'Location': 7,
            'Other': 8
        }

    def getParameterInfo(self):
        # SRGD_Input_File
        input_csv = arcpy.Parameter()
        input_csv.name = u'SRGD_Input_File'
        input_csv.displayName = u'SRGD Input File'
        input_csv.parameterType = 'Required'
        input_csv.direction = 'Input'
        input_csv.datatype = u'File'

        # Spatial_Reference
        sr = arcpy.Parameter()
        sr.name = u'Spatial_Reference'
        sr.displayName = u'Spatial Reference'
        sr.parameterType = 'Optional'
        sr.direction = 'Input'
        sr.datatype = u'Spatial Reference'

        # File_Geodatabase_Location
        output_loc= arcpy.Parameter()
        output_loc.name = u'File_Geodatabase_Location'
        output_loc.displayName = u'File Geodatabase Location'
        output_loc.parameterType = 'Required'
        output_loc.direction = 'Input'
        output_loc.datatype = u'Folder'

        # File_Geodatabase_Name
        output_gdb= arcpy.Parameter()
        output_gdb.name = u'File_Geodatabase_Name'
        output_gdb.displayName = u'File Geodatabase Name'
        output_gdb.parameterType = 'Required'
        output_gdb.direction = 'Input'
        output_gdb.datatype = u'String'

        # Output_Feature_Class
        output_fc= arcpy.Parameter()
        output_fc.name = u'Output_Feature_Class'
        output_fc.displayName = u'Output Feature Class'
        output_fc.parameterType = 'Required'
        output_fc.direction = 'Input'
        output_fc.datatype = u'String'

        # genetic columns
        genetic = arcpy.Parameter()
        genetic.name = u'Genetic_Columns'
        genetic.displayName = u'Genetic Columns'
        genetic.parameterType = 'Required'
        genetic.direction = 'Input'
        genetic.multiValue = True
        genetic.filter.list = ['Sex', 'Haplotype', 'L_locus1', 'L_locus2']

        # identification columns
        identification = arcpy.Parameter()
        identification.name = 'Identification_Columns'
        identification.displayName = 'Identification Columns'
        identification.parameterType = 'Required'
        identification.direction = 'Input'
        identification.multiValue = True
        identification.filter.list = ['Sample_ID', 'Individual_ID']

        # location columns
        loc = arcpy.Parameter()
        loc.name = u'Location_Columns'
        loc.displayName = u'Location Columns'
        loc.parameterType = 'Required'
        loc.direction = 'Input'
        loc.multiValue = True
        loc.filter.list = ['Latitude', 'Longitude']

        # other columns
        other = arcpy.Parameter()
        other.name = u'Other_Columns'
        other.displayName = u'Other Columns'
        other.parameterType = 'Optional'
        other.direction = 'Input'
        other.multiValue = True
        other.filter.list = ['Region', 'Date_Time']
        
        return [input_csv, sr, output_loc, output_gdb, output_fc, genetic, identification, loc, other]

    def isLicensed(self):
        return True

    def updateDynamicFilters(self, filter_param, update_param, unused_values):
        result = []
        # ValueTable object; 
        # http://help.arcgis.com/en/arcgisdesktop/10.0/help/000v/000v000000q1000000.htm
        filter_val = filter_param.value
        if filter_val is not None:
            filter_values = filter_val.exportToString().split(";")

            for param in unused_values:
                if param not in filter_values:
                    result.append(param)
            
            update_param.filter.list = result
        return result

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)

        dynamic_cols = ['Genetic', 'Identification', 'Location', 'Other']
        unused_values = []

        if parameters[self.cols['input_csv']] is not None:
            #f = open('genegis.log', 'w')
            input_table_name = parameters[self.cols['input_csv']].valueAsText
            # read the validated header
            (header, data, dialect) = utils.validated_table_results(input_table_name)
            # create a duplicate list; but a copy so we can modify the list as we go
            unused_values = list(header)
            # map search strings to variable groups, include 'protected'
            # column to explicitly define type for these columns
            group_expressions= [
               #  group     regex    column type
                ('Genetic', '^sex$', 'Text'),
                ('Genetic', '^haplotype$', 'Text'),
                ('Genetic', '^dlphap$', 'Text'),
                ('Genetic', '^l_', None), 
                ('Identification', '_id$', 'Text'),
                ('Location', '^x$', None), 
                ('Location', '^y$', None),
                ('Location', 'longitude', None),
                ('Location', 'latitude', None)
            ]

            # assign 'known' values based on some inference
            #f.write("Initial header: %s\n" % header)

            # A little tricky: implement unique result lists for each of
            # our group types.
            results = dict(((group,[]) for group in dynamic_cols))
            for (group, expr, data_type) in group_expressions:
                #f.write("current list of unused values at expr %s [%s]: %s\n" % (expr, group, unused_values))
                for (i, value) in enumerate(header):
                    if re.search(expr, value, re.IGNORECASE):
                        #f.write("FOUND: %s in group %s\n" % (value, group))
                        results[group].append(value)
                        unused_values.remove(value)
                        # if a data type is defined for this column,
                        # record it so we can force a mapping.
                        if data_type is not None:
                            config.protected_columns[value] = (i + 1, data_type)
                    #else:
                    #    f.write("NOT FOUND: %s in group %s\n" % (value, group))
                # modify the resulting attribute column list
                #f.write("Applying final filtered list of %s to group %s\n" % (results, group))

            # any remaining attributes should be included under 'Other'
            results['Other'] = unused_values

            # update the lists provided to the user 
            for (group, vals) in results.items():
                parameters[self.cols[group]].filter.list = vals
                parameters[self.cols[group]].value = vals
            #f.write("Unused values remaining: %s\n" % unused_values) 
            
            
            # try modifying our first attribute columns list
            parameters[cols['Genetic']].filter.list = unused_values

        # select each set of columns and filter dependent lists
        """
        for i, label in enumerate(dynamic_cols[1:]):
            update_label = self.cols[label]
            filter_label = self.cols[dynamic_cols[i]]
            #f.write("Running with: {0} {1} {2}\n\n".format(update_label,
            #    filter_label, ",".join(unused_values)))
            unused_values = self.updateDynamicFilters(
                    parameters[filter_label], 
                    parameters[update_label], 
                    unused_values)
        """
        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        in_table = parameters[self.cols['input_csv']]
        if in_table is not None:
            input_table_name = in_table.valueAsText
            # read the original data
            (orig_header, orig_data, orig_dialect) = utils.parse_table(input_table_name)
            # read the validated header
            (header, data, dialect) = utils.validated_table_results(input_table_name)

            # check if we've modified the header. 
            if orig_header != header:
                modified_columns = []
                # find which columns have been changed
                for (i, column) in enumerate(header):
                    orig_column = orig_header[i]
                    if orig_column != column:
                        modified_columns.append((orig_column, column))
                modified_result = [" was modified to ".join(c) for c in modified_columns]
                msg = "Headers were modified based on ArcGIS field name restrictions:\n" \
                      + "\n".join(modified_result)
                parameters[0].setWarningMessage(msg)
         
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        from scripts import ClassifiedImport
        # if the script is running within ArcGIS as a tool, get the following
        # user defined parameters
        ClassifiedImport.main(
            input_table=parameters[0].valueAsText,
            sr=parameters[1].valueAsText,
            output_loc=parameters[2].valueAsText,
            output_gdb=parameters[3].valueAsText,
            output_fc=parameters[4].valueAsText,
            genetic=parameters[5].valueAsText,
            identification=parameters[6].valueAsText,
            location=parameters[7].valueAsText,
            other=parameters[8].valueAsText,
            protected_map=config.protected_columns)
        
class extractRasterByPoints(object):
    class ToolValidator:
      """Class for validating a tool's parameter values and controlling
      the behavior of the tool's dialog."""
    
      def __init__(self, parameters):
        """Setup arcpy and the list of tool parameters."""
        import arcpy
        self.params = parameters
    
      def initializeParameters(self):
        """Refine the properties of a tool's parameters.  This method is
        called when the tool is opened."""
        return
    
      def updateParameters(self):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parmater
        has been changed."""
        return
    
      def updateMessages(self):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return
    
    def __init__(self):
        self.label = u'Extract Raster Values'
        self.description = u'This tool allows extraction of one or more rasters at our sample locations.'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Raster Input
        # FIXME: only handles one raster currently
        input_raster = arcpy.Parameter()
        input_raster.name = u'Input_Raster'
        input_raster.displayName = u'Input Raster'
        input_raster.parameterType = 'Required'
        input_raster.direction = 'Input'
        input_raster.datatype = u'Raster Dataset'
        input_raster.multiValue = False
        """
        # FIXME: re-enable multiple input rasters; issue #2
        input_raster.multiValue = True
        if config.all_layers is not None:
            filter_list = []
            for layer in config.all_layers:
                try:
                    desc = arcpy.Describe(layer)
                    if desc.datasetType == 'RasterDataset':
                        filter_list.append(layer)
                except:
                    # silently skip layers which don't support describe (e.g. AGOL).
                    continue
                input_raster.filter.list = filter_list
        """
        # Output_Feature_Table
        output_ft= arcpy.Parameter()
        output_ft.name = u'Output_Feature_Table'
        output_ft.displayName = u'Output Feature Table'
        output_ft.parameterType = 'Required'
        output_ft.direction = 'Output'
        output_ft.datatype = u'Table'

        return [input_raster, output_ft]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)

        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        messages.addMessage("got selected layer: %s" % config.selected_layer)
        input_raster = parameters[0].valueAsText
        selected_layer = config.selected_layer
        output_table = parameters[1].valueAsText
        messages.addMessage("executing Sample on %i rasters..." % 1)
        messages.addMessage("using preselected point layer, '%s'" % selected_layer)
        arcpy.CheckOutExtension("Spatial")
        arcpy.sa.Sample([input_raster], selected_layer.dataSource, output_table, "NEAREST")

class ExportGenAlEx(object):
    class ToolValidator:
      """Class for validating a tool's parameter values and controlling
      the behavior of the tool's dialog."""
    
      def __init__(self, parameters):
        """Setup arcpy and the list of tool parameters."""
        import arcpy
        self.params = parameters
    
      def initializeParameters(self):
        """Refine the properties of a tool's parameters.  This method is
        called when the tool is opened."""
        return
    
      def updateParameters(self):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parmater
        has been changed."""
        return
    
      def updateMessages(self):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return
    
    def __init__(self):
        self.label = u'Export to GenAlex_CodominantData'
        self.description = u'This tool allows the user to export data to a comma separated text file that follows the required input format for GenAlEx (Peakall and Smouse 2006), a Microsoft Excel Add-In.\r\n\r\nGenAlEx is available from:\r\n\r\nhttp://www.anu.edu.au/BoZo/GenAlEx/\r\n'
        self.canRunInBackground = False
    def getParameterInfo(self):
        # Input_Feature_Class
        input_features = arcpy.Parameter()
        input_features.name = u'Input_Feature_Class'
        input_features.displayName = u'Input Feature Class'
        input_features.parameterType = 'Required'
        input_features.direction = 'Input'
        input_features.datatype = u'Feature Layer'

        # Where_Clause
        where_clause = arcpy.Parameter()
        where_clause.name = u'Where_Clause'
        where_clause.displayName = u'Where Clause'
        where_clause.parameterType = 'Optional'
        where_clause.direction = 'Input'
        where_clause.datatype = u'SQL Expression'

        # Attribute_Field__to_order_by_population_
        order_by = arcpy.Parameter()
        order_by.name = u'Attribute_Field_to_order_by_population_'
        order_by.displayName = u'Attribute Field (to order by population)'
        order_by.parameterType = 'Optional'
        order_by.direction = 'Input'
        order_by.datatype = u'Field'

        """
        # Output_File_Location
        output_location = arcpy.Parameter()
        output_location.name = u'Output_File_Location'
        output_location.displayName = u'Output File Location'
        output_location.parameterType = 'Required'
        output_location.direction = 'Input'
        output_location.datatype = u'Folder'

        # Output_File_Name
        param_5 = arcpy.Parameter()
        param_5.name = u'Output_File_Name'
        param_5.displayName = u'Output File Name'
        param_5.parameterType = 'Required'
        param_5.direction = 'Input'
        param_5.datatype = u'String'
        """

        # Output_File_Location
        output_name = arcpy.Parameter()
        output_name.name = u'Output_File'
        output_name.displayName = u'Output File'
        output_name.parameterType = 'Required'
        output_name.direction = 'Output'
        output_name.datatype = u'File'

        return [input_features, where_clause, order_by, output_name]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        from scripts import ExportGenAlEx
        # if the script is running within ArcGIS as a tool, get the following
        # user defined parameters:  
        ExportGenAlEx.main(
            input_features=parameters[0].valueAsText,
            where_clause=parameters[1].valueAsText,
            order_by=parameters[2].valueAsText,
            output_name=parameters[3].valueAsText)
            

class SelectDataByAttributes(object):
    class ToolValidator:
      """Class for validating a tool's parameter values and controlling
      the behavior of the tool's dialog."""
    
      def __init__(self, parameters):
        """Setup arcpy and the list of tool parameters."""
        import arcpy
        self.params = parameters
    
      def initializeParameters(self):
        """Refine the properties of a tool's parameters.  This method is
        called when the tool is opened."""
        return
    
      def updateParameters(self):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parmater
        has been changed."""
        return
    
      def updateMessages(self):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return
    
    def __init__(self):
        self.label = u'Select Data By Attributes'
        self.canRunInBackground = False
    def getParameterInfo(self):
        # Input_Feature_Class
        param_1 = arcpy.Parameter()
        param_1.name = u'Input_Feature_Class'
        param_1.displayName = u'Input Feature Class'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Feature Layer'

        # Selection_Type
        param_2 = arcpy.Parameter()
        param_2.name = u'Selection_Type'
        param_2.displayName = u'Selection Type'
        param_2.parameterType = 'Required'
        param_2.direction = 'Input'
        param_2.datatype = u'String'
        param_2.filter.list = [u'NEW_SELECTION']

        # SQL_Expression
        param_3 = arcpy.Parameter()
        param_3.name = u'SQL_Expression'
        param_3.displayName = u'SQL Expression'
        param_3.parameterType = 'Required'
        param_3.direction = 'Input'
        param_3.datatype = u'SQL Expression'

        # Selection_Type_2
        param_4 = arcpy.Parameter()
        param_4.name = u'Selection_Type_2'
        param_4.displayName = u'Selection Type 2'
        param_4.parameterType = 'Optional'
        param_4.direction = 'Input'
        param_4.datatype = u'String'
        param_4.filter.list = [u'ADD_TO_SELECTION', u'SUBSET_SELECTION']

        # SQL_Expression_2
        param_5 = arcpy.Parameter()
        param_5.name = u'SQL_Expression_2'
        param_5.displayName = u'SQL Expression 2'
        param_5.parameterType = 'Optional'
        param_5.direction = 'Input'
        param_5.datatype = u'SQL Expression'

        # Selection_Type_3
        param_6 = arcpy.Parameter()
        param_6.name = u'Selection_Type_3'
        param_6.displayName = u'Selection Type 3'
        param_6.parameterType = 'Optional'
        param_6.direction = 'Input'
        param_6.datatype = u'String'
        param_6.filter.list = [u'ADD_TO_SELECTION', u'SUBSET_SELECTION']

        # SQL_Expression_3
        param_7 = arcpy.Parameter()
        param_7.name = u'SQL_Expression_3'
        param_7.displayName = u'SQL Expression 3'
        param_7.parameterType = 'Optional'
        param_7.direction = 'Input'
        param_7.datatype = u'SQL Expression'

        # Output_Feature_Class_Location
        param_8 = arcpy.Parameter()
        param_8.name = u'Output_Feature_Class_Location'
        param_8.displayName = u'Output Feature Class Location'
        param_8.parameterType = 'Required'
        param_8.direction = 'Input'
        param_8.datatype = u'Workspace'

        # Output_Feature_Class_Name
        param_9 = arcpy.Parameter()
        param_9.name = u'Output_Feature_Class_Name'
        param_9.displayName = u'Output Feature Class Name'
        param_9.parameterType = 'Required'
        param_9.direction = 'Input'
        param_9.datatype = u'String'

        # Log_File_Location
        param_10 = arcpy.Parameter()
        param_10.name = u'Log_File_Location'
        param_10.displayName = u'Log File Location'
        param_10.parameterType = 'Required'
        param_10.direction = 'Input'
        param_10.datatype = u'Folder'

        return [param_1, param_2, param_3, param_4, param_5, param_6, param_7, param_8, param_9, param_10]
    def isLicensed(self):
        return True
    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateParameters()
    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()
    def execute(self, parameters, messages):
        with script_run_as(u'C:\\data\\arcgis\\toolboxes\\geneGIS_29July2012\\Scripts\\SelectByAttributes.py'):
            # ------------------------------------------------------------------------------------------------------
            # SelectByAttributes.py
            #
            # Created by: Dori Dick
            #             College of Earth, Ocean and Atmospheric Sciences
            #             Oregon State Univeristy
            #
            # Created on: 20 April 2012
            # Last modified: 26 April 2012
            # 
            # Description: This script allows the user to perform up to 3 Select By Attribute selections on an input 
            #                     feature class and then exports the selected records to a new feature class.  A log text
            #                     file is also created providing a record of the inputs and outputs from the tool run.  For
            #                     easy reference, the log file will have the same name as the output feature class.
            #
            #                     Selections are based on the attribute fields of the feature class and use a SQL 
            #                     expression for the selection criteria.  The first selection is required and considered to be
            #                     a "NEW_SELECTION".  The other  two selections are optional.  
            #
            #                     There are 3 selection types available to use with this tool:
            #                            1. NEW_SELECTION = The resulting selection; replaces any previous existing selection
            #                            2. ADD_TO_SELECTION = The resulting selection is added to an existing selection. 
            #                                                                           If no selection exists, it acts like a NEW_SELECTION
            #                            3. SUBSET_SELECTION = The resulting selection is combined with an existing selection; only
            #                                                                          records common to both are retained.  
            #
            # Required Inputs: An existing Feature Class containing spatially referenced genetic data 
            #                           A NEW_SELECTION SQL expression
            #                           An output location (geodatabase) and name for the newly created feature class.  
            #                           An output location where the log file will be written (NOTE: this file willl have the same name
            #                                  as the output feature class.)
            #
            # Optional Inputs: A second and third selection type and assicated SQL expression
            #
            # Script Outputs: A new geodatabase feature class and a log text file - both with the same name to allow for easy
            #                                 reference
            #              
            # This script was developed to work with ArcGIS 10 and Python 2.6 installed during ArcGIS installation. 
            #
            # ------------------------------------------------------------------------------------------------------
            
            # Import arcpy and datetime modules
            try:    
                import arcpy
                from datetime import datetime
                #import UniqueValue
            
            except:
                print "Error importing modules"
                print arcpy.GetMessages()
                
            messages.AddMessage("Arcpy and datetime modules successfully imported.")
            
            print "All needed modules (arcpy, datetime) imported successfully."
            
            arcpy.env.overwriteOutput = 1
            
            # Setting a boolean statement.  NOTE: The default is set to True so that it will run as a tool within ArcGIS.  
            # To run the script outside of ArcGIS, change to False in the next line of code
            RunningWithArcGISGUI = (True)
            
            try:
                # if the script is running within ArcGIS as a tool, get the following user defined parameters: 
                if (RunningWithArcGISGUI) == (True):            
                    
                    # The Input Feature Class
                    Parameter1 = parameters[0].valueAsText 
                    
                    # Output Layer -- a temporary layer from which the selections are made. 
                    # NOTE: This file is deleted automatically when the script finishes
                    Parameter2 = "TempLayer"
                  
                    # Selection Type 1 -- The first selection must be a NEW_SELECTION
                    # This user input is required in order for the tool to run
                    Parameter3 = parameters[1].valueAsText
                    
                    # SQL expression 1 -- The string statement, in SQL code, that will be used to select 
                    # the desired records
                    Parameter4 = parameters[2].valueAsText
                     
                    # Selection Type 2  -- A second selection that can be either ADD_TO_SELECTION or 
                    # SUBSET_SELECTION   
                    # NOTE: This selection is optional
                    Parameter5 = parameters[3].valueAsText
                    
                    # SQL statement 2 -- The string statement, in SQL code, that will be used to select 
                    # the desired records
                    Parameter6 = parameters[4].valueAsText
                    
                    # Selection Type 3 -- A third selection that can be either ADD_TO_SELECTION or 
                    # SUBSET_SELECTION   
                    # NOTE: This selection is optional    
                    Parameter7 = parameters[5].valueAsText
                    
                    # SQL statement 3 -- The string statement, in SQL code, that will be used to select 
                    # the desired records
                    Parameter8 = parameters[6].valueAsText
                    
                     # Location of Output Feature Class -- This must be a location within a geodatabase
                    Parameter9 = parameters[7].valueAsText
                    
                    # Output Feature Class Name
                    Parameter10 = parameters[8].valueAsText
                    
                    # Location of log text file created for this tool run
                    Parameter11 = parameters[9].valueAsText    
                
            # if the script is NOT running within ArcGIS as a tool, please define the following parameters by hard 
            # coding all the inputs below EXCEPT Parameter2
                else:       
                    # The Input Feature Class
                    Parameter1 =  "C:\\geneGIS\\WorkingFolder\\test_20March.gdb\\SPLASH_Whales"
                    
                    # Output Layer -- a temporary layer from which the selections are made. 
                    # NOTE: This file is deleted automatically when the script finishes
                    Parameter2 = "TempLayer"
                    
                    # Selection Type 1 -- The first selection must be a NEW_SELECTION
                    # This user input is required in order for the tool to run
                    Parameter3 = "NEW_SELECTION"
                    
                    # SQL expression 1 -- The string statement, in SQL code, that will be used to select 
                    # the desired records
                    Parameter4 =  "\"Haplotype\" = 'E1'"
                    
                    # Selection Type 2  -- A second selection that can be either ADD_TO_SELECTION or 
                    # SUBSET_SELECTION   
                    Parameter5 = "SUBSET_SELECTION"
                    
                     # SQL statement 2 -- The string statement, in SQL code, that will be used to select 
                    # the desired records
                    Parameter6 = "\"Area\" ='CA-OR'"
                    
                    # Selection Type 3 -- A third selection that can be either ADD_TO_SELECTION or 
                    # SUBSET_SELECTION   
                    Parameter7 = "SUBSET_SELECTION"
                    
                    # SQL statement 3 -- The string statement, in SQL code, that will be used to select 
                    # the desired records
                    Parameter8 = "\"Sex\" = 'F'"
                    
                    # Location of Output Feature Class -- This must be a location within a geodatabase
                    Parameter9 = "C:\\geneGIS\\WorkingFolder\\test_20March.gdb"
                    
                    # Output Feature Class Name
                    Parameter10 = "test_selection"     
                    
                    # Location of log text file created for this tool run
                    Parameter11 = "C:\\geneGIS\\WorkingFolder"
                    
            except:
                print ("Error setting tool parameters")
                print arcpy.GetMessages()
            
            print "Parameters successfully defined!"
            messages.AddMessage("Parameters Successfully defined!")
            
            try:
                
                # Process: Make Feature Layer.  This layer is temporary and will be deleted upon script completion.
                # SYNTAX: MakeFeatureLayer_management (in_features, out_layer, {where_clause}, {workspace}, {field_info})
                arcpy.MakeFeatureLayer_management(Parameter1, Parameter2, "", "", "")  
                
            except:
                print ("Error setting tool parameters")
                print arcpy.GetMessages()
            messages.AddMessage("Make Feature Layer completed")
            
            try:
                # Process: Select Layer By Attribute
                # SYNTAX: SelectLayerByAttribute_management (in_layer_or_view, {selection_type}, {where_clause})
                arcpy.SelectLayerByAttribute_management(Parameter2, Parameter3, Parameter4)
            
            except:
                print("Unable to complete Select Layer by Attribute")
                print arcpy.GetMessages()
            messages.AddMessage("Select Layer By Attribute 1 successfully completed!")
            
            try:
                # if Selection Type 2 (Parameter5) is not blank, conduct the following selection, otherwise pass
                if Parameter5 <> "":              
                    
                    # Process: Select Layer By Attribute
                    # SYNTAX: SelectLayerByAttribute_management (in_layer_or_view, {selection_type}, {where_clause})        
                    arcpy.SelectLayerByAttribute_management(Parameter2, Parameter5, Parameter6)
                    
                else:
                    pass
                
            except:
                    print("Unable to complete Select Layer by Attribute")
                    print arcpy.GetMessages()
            messages.AddMessage("Select Layer By Attribute 2 successfully completed!")
            
            try:
                # if Selection Type 3 (Parameter7) is not blank, conduct the following selection, otherwise pass
                if Parameter7 <> "":
                    
                    # Process: Select Layer By Attribute
                    # SYNTAX: SelectLayerByAttribute_management (in_layer_or_view, {selection_type}, {where_clause})         
                    arcpy.SelectLayerByAttribute_management(Parameter2, Parameter7, Parameter8)
                    
                else:
                    pass
                
            except:
                    print("Unable to complete Select Layer by Attribute")
                    print arcpy.GetMessages()
            messages.AddMessage("Select Layer By Attribute 3 successfully completed!")
            
            try:
                
                # Process: Copy Features
                # SYNTAX: CopyFeatures_management (in_features, out_feature_class, {config_keyword}, {spatial_grid_1}, {spatial_grid_2}, {spatial_grid_3})
                arcpy.CopyFeatures_management(Parameter2, Parameter9 + "\\" + Parameter10, "", "0", "0", "0")
            
            except:
                print("Unable to copy features to a new feature class")
                print arcpy.GetMessages()
            messages.AddMessage("Selected records copied to a new feature class")
            
            
            # Create and open a log text file that will contain the details of the current tool run 
            OutputFile = open(Parameter11 + "\\" + Parameter10 + ".txt", "w")
            
            OutputFile.write("\n")
            OutputFile.write("*** Details from running the tool \"Select Data By Attributes\" ***" )
            OutputFile.write("\n")
            OutputFile.write("\n")
            OutputFile.write("\n")
            OutputFile.write("Select Data by Attributes Tool was run on: " + str(datetime.now())) 
            OutputFile.write("\n")
            OutputFile.write("\n")
            OutputFile.write("Input Feature Class used: " + Parameter1)
            OutputFile.write("\n")
            OutputFile.write("\n")
            OutputFile.write("First Selection Type used: " + Parameter3)
            OutputFile.write("\n")
            OutputFile.write("\n")
            OutputFile.write("First Selection SQL statement: " + Parameter4)
            OutputFile.write("\n")
            OutputFile.write("\n")
            OutputFile.write("Second Selection Type used: " + Parameter5)
            OutputFile.write("\n")
            OutputFile.write("\n")
            OutputFile.write("Second Selection SQL statement: " + Parameter6)
            OutputFile.write("\n")
            OutputFile.write("\n")
            OutputFile.write("Third Selection Type used: " + Parameter7)
            OutputFile.write("\n")
            OutputFile.write("\n")
            OutputFile.write("Third Selection SQL statement: " + Parameter8)
            OutputFile.write("\n")
            OutputFile.write("\n")
            OutputFile.write("Output Feature Class: " + Parameter9 + "\\" + Parameter10)
            OutputFile.write("\n")
            OutputFile.write("\n")
            OutputFile.write("Log File: " + Parameter11+ "\\" + Parameter10 + ".txt")
            
            print ("Done!")
