# -*- coding: utf-8 -*-

import csv
import os
import re
import sys
import time

import arcpy

# enable local imports; allow importing both this directory and one above
local_path = os.path.dirname(__file__)
for path in [local_path, os.path.join(local_path, '..')]:
    full_path = os.path.abspath(path)
    sys.path.insert(0, os.path.abspath(path))

# addin specific configuration and utility functions
import utils as addin_utils
import config

# import utilities & config from our scripts as well
from scripts import utils

class Toolbox(object):
    def __init__(self):
        self.label = u'geneGIS_Jan_2013'
        self.alias = ''
        self.tools = [
            ClassifiedImport, # import data from SRGD file
            SelectDataByAttributes, # filter data
            ExtractRasterByPoints, # extract values at point locations
            # Export routines; get our data elsewhere
            ExportGenAlEx, # GenAlEx, Excel analysis tool
            ExportGenepop, # Genepop, population differentiation statistics
            ExportSRGD # SRGD without Geodatabase columns; for Shepard interchange
        ]
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
        output_fc.parameterType = 'Derived'
        output_fc.direction = 'Output'
        output_fc.datatype = u'DEFeatureClass'
        output_fc.parameterDependencies = [output_loc.name, output_gdb.name]

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

        input_table_name = parameters[self.cols['input_csv']].valueAsText
        output_loc = parameters[self.cols['output_loc']].valueAsText
        output_gdb = parameters[self.cols['output_gdb']].valueAsText
        output_fc = parameters[self.cols['output_fc']].valueAsText

        if input_table_name is not None:
            #f = open('genegis.log', 'w')
            # read the validated header
            (header, data, dialect) = utils.validated_table_results(input_table_name)
            # create a duplicate list; but a copy so we can modify the list as we go
            unused_values = list(header)

            # assign 'known' values based on some inference
            #f.write("Initial header: %s\n" % header)

            # A little tricky: implement unique result lists for each of
            # our group types.
            results = dict(((group,[]) for group in dynamic_cols))
            for (group, expr, data_type) in config.group_expressions:
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

        if output_loc is not None and input_table_name is not None and output_gdb is not None:
            # derive the output feature class name if these two parameters are set
            (label, ext) = os.path.splitext(os.path.basename(input_table_name))
            output_fc_path = os.path.join(output_loc, "%s.gdb" % output_gdb, "%s_Spatial" % label)
            parameters[self.cols['output_fc']].value = output_fc_path

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
        input_table_name = parameters[self.cols['input_csv']].valueAsText
        if input_table_name is not None:
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

        return

class ExtractRasterByPoints(object):
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
        self.label = u'Extract Raster Values To Points'
        self.description = u'This tool allows extraction of one or more rasters at our sample locations.'
        self.canRunInBackground = False
        self.cols = {
            'input_raster': 0,
            'input_fc': 1
        }

    def getParameterInfo(self):
        # FIXME: Doesn't run if the user hasn't selected a layer in the combobox. Either throw an error before they run the tool, or let them fill it out, but populate it if they've selected a layer.

        # Raster Input
        input_raster = arcpy.Parameter()
        input_raster.name = u'Input_Raster'
        input_raster.displayName = u'Input Raster(s)'
        input_raster.parameterType = 'Required'
        input_raster.direction = 'Input'
        input_raster.datatype = u'Raster Dataset'
        input_raster.multiValue = True

        selected_layer = None
        # check if we have a layer selected from the combo box 
        if config.selected_layer is not None:
            selected_layer = config.selected_layer.dataSource
        elif config.settings.fc_path != '':
            selected_layer = config.settings.fc_path 
 
        # Output Feature Class
        input_fc = arcpy.Parameter()
        input_fc.name = u'Input_Feature_Class'
        input_fc.displayName = u'Feature Class (will add columns for extracted raster results)'
        input_fc.direction = 'Input'
        input_fc.parameterType = 'Required'
        input_fc.datatype = u'DEFeatureClass'
        input_fc.value = selected_layer

        return [input_raster, input_fc]

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
        from scripts import ExtractRasterValuesToPoints       

        # if the script is running within ArcGIS as a tool, get the following
        # user defined parameters
        ExtractRasterValuesToPoints.main(
            input_raster=parameters[0].valueAsText,
            selected_layer=parameters[1].valueAsText)


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
        validation is performed.  This method is called whenever a parameter
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
        where_clause.datatype = u'SQL Expression'
        where_clause.parameterType = 'Optional'
        where_clause.direction = 'Input'        
        where_clause.Obtainedfrom= input_features

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
        from scripts import ExportToGenAlEx
        # if the script is running within ArcGIS as a tool, get the following
        # user defined parameters:  
        ExportToGenAlEx.main(
            input_features=parameters[0].valueAsText,
            where_clause=parameters[1].valueAsText,
            order_by=parameters[2].valueAsText,
            output_name=parameters[3].valueAsText)
        
class ExportGenepop(object):
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
        self.label = u'Export to Genepop'
        self.description = u'This tool allows the user to export data to a text file that follows the required input format for Genepop (Raymond and Rousset 1995; Rousset 2008).  For more information see: \r\n\r\nhttp://genepop.curtin.edu.au/\r\n'
        self.canRunInBackground = False
        self.cols = {
            'input_features': 0,
            'where_clause': 1,
            'order_by': 2,
            'output_name': 3
        }

    def getParameterInfo(self):
        # Input_Feature_Class
        input_features = arcpy.Parameter()
        input_features.name = u'Input_Feature_Class'
        input_features.displayName = u'Input Feature Class'
        input_features.parameterType = 'Required'
        input_features.direction = 'Input'
        input_features.datatype = 'Feature Layer'
        
        # Where_Clause
        where_clause = arcpy.Parameter()
        where_clause.name = u'Where_Clause'
        where_clause.displayName = u'Where Clause'
        where_clause.parameterType = 'Optional'
        where_clause.direction = 'Output'
        where_clause.datatype = u'SQL Expression'
        where_clause.parameterDependencies= [input_features.name] 
        
        # Attribute_Field__to_order_by_population_
        order_by = arcpy.Parameter()
        order_by.name = u'Attribute_Field_to_order_by_population_'
        order_by.displayName = u'Attribute Field (to order by population)'
        order_by.parameterType = 'Required'
        order_by.direction = 'Input'
        order_by.datatype = u'Field'
        order_by.parameterDependencies=[input_features.name]

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

        output_name = parameters[self.cols['output_name']].valueAsText
        if output_name is not None:
            # make sure the output file name has a TXT extension.
            output_name = utils.add_file_extension(output_name, 'txt')
            parameters[self.cols['output_name']].value = output_name

        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        from scripts import ExportToGenepop

        # if the script is running within ArcGIS as a tool, get the following
        # user defined parameters
        ExportToGenepop.main(
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
        validation is performed.  This method is called whenever a parameter
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
        from scripts import SelectByAttributes 
        # if the script is running within ArcGIS as a tool, get the following
        # user defined parameters:  
        SelectByAttributes.main(
            xx=parameters[0].valueAsText,
            yy=parameters[1].valueAsText,
            zz=parameters[2].valueAsText,
            aa=parameters[3].valueAsText)

class ExportSRGD(object):
    def __init__(self):
        self.label = u'Export SRGD File'
        self.description = u'Export SRGD results.'
        self.canRunInBackground = False
        self.cols = {
            'input_feature': 0,
            'output_csv': 1
        }

    def getParameterInfo(self):
        input_feature = arcpy.Parameter()
        input_feature.name = 'Input_Feature'
        input_feature.displayName = 'Input Feature'
        input_feature.parameterType = 'Required'
        input_feature.direction = 'Input'
        input_feature.datatype = 'GPFeatureLayer'

        # Output_CSV
        output_csv= arcpy.Parameter()
        output_csv.name = u'Output_SRGD_File'
        output_csv.displayName = u'Output SRGD CSV File'
        output_csv.parameterType = 'Required'
        output_csv.direction = 'Output'
        output_csv.datatype = u'File'

        return [input_feature, output_csv]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)

        output_csv = parameters[self.cols['output_csv']].valueAsText
        if output_csv is not None:
            # make sure the output file name has a CSV extension.
            output_csv = utils.add_file_extension(output_csv, 'csv')
            parameters[self.cols['output_csv']].value = output_csv

        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        input_feature = parameters[0].valueAsText
        output_csv = parameters[1].valueAsText 
        arcpy.env.addOutputsToMap  = False
        # run export on this feature class.
        messages.addMessage("Running export...")
        addin_utils.writeToSRGD(input_feature, output_csv)
        messages.addMessage("Exported results saved to %s." % output_csv)
        time.sleep(4)
