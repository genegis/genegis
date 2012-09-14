# -*- coding: utf-8 -*-

import contextlib
import csv
import os
import sys

import arcpy

# You can ignore/delete this code; these are basic utility functions to
# streamline porting

@contextlib.contextmanager
def script_run_as(filename, args=None):
    oldpath = sys.path[:]
    oldargv = sys.argv[:]
    newdir = os.path.dirname(filename)
    sys.path = oldpath + [newdir]
    sys.argv = [filename] + [arg.valueAsText for arg in (args or [])]
    oldcwd = os.getcwdu()
    os.chdir(newdir)

    try:
        # Actually run
        yield filename
    finally:
        # Restore old settings
        sys.path = oldpath
        sys.argv = oldargv
        os.chdir(oldcwd)

def set_parameter_as_text(params, index, val):
    if (hasattr(params[index].value, 'value')):
        params[index].value.value = val
    else:
        params[index].value = val

# Export of toolbox C:\data\arcgis\toolboxes\geneGIS_29July2012\geneGIS_29July2012.tbx

class Toolbox(object):
    def __init__(self):
        self.label = u'geneGIS_29July2012'
        self.alias = ''
        self.tools = [csvtofeatureclass, ExportGenAlex2, ExportGenAlex3, SelectDataByAttributes, classifiedimport]

# Tool implementation code

class csvtofeatureclass(object):
    """C:\data\arcgis\toolboxes\geneGIS_29July2012\geneGIS_29July2012.tbx\csvtofeatureclass"""
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
        self.label = u'csv to feature class'
        self.description = u'This tool allows the user to covert an input file (formated with the SRGD.csv specifications) to a feature class within a file geodatabse.'
        self.canRunInBackground = False
    def getParameterInfo(self):
        # SRGD_Input_File
        param_1 = arcpy.Parameter()
        param_1.name = u'SRGD_Input_File'
        param_1.displayName = u'SRGD Input File'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'File'

        # Spatial_Reference
        param_2 = arcpy.Parameter()
        param_2.name = u'Spatial_Reference'
        param_2.displayName = u'Spatial Reference'
        param_2.parameterType = 'Optional'
        param_2.direction = 'Input'
        param_2.datatype = u'Spatial Reference'

        # File_Geodatabase_Location
        param_3 = arcpy.Parameter()
        param_3.name = u'File_Geodatabase_Location'
        param_3.displayName = u'File Geodatabase Location'
        param_3.parameterType = 'Required'
        param_3.direction = 'Input'
        param_3.datatype = u'Folder'

        # File_Geodatabase_Name
        param_4 = arcpy.Parameter()
        param_4.name = u'File_Geodatabase_Name'
        param_4.displayName = u'File Geodatabase Name'
        param_4.parameterType = 'Required'
        param_4.direction = 'Input'
        param_4.datatype = u'String'

        # Output_Feature_Class
        param_5 = arcpy.Parameter()
        param_5.name = u'Output_Feature_Class'
        param_5.displayName = u'Output Feature Class'
        param_5.parameterType = 'Required'
        param_5.direction = 'Input'
        param_5.datatype = u'String'

        return [param_1, param_2, param_3, param_4, param_5]
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
        with script_run_as(u'C:\\data\\arcgis\\toolboxes\\geneGIS_29July2012\\Scripts\\CsvToFeatureClass.py'):
            # ------------------------------------------------------------------------------------------------------
            # CsvToFeatureClass.py
            #
            # Created by: Dori Dick
            #             College of Earth, Ocean and Atmospheric Sciences
            #             Oregon State Univeristy
            #
            # Created on: 3 March 2012
            # Last modified: 3 April 2012
            # 
            # Description: This script converts spatially reference genetic data from a simple flat file format
            #              to a Feature Class viewable in ArcGIS 10.  
            #
            # Required Inputs: Spatially referenced genetic data formatted according to the SRDG.csv file format 
            #                  This data can be for indentifed individuals or for genetic samples.
            #
            # Optional Inputs: If known, a spatial reference for the point data (recommended)
            #
            # Script Outputs: a new File Geodatabase
            #                 a new feature class located within the File Geodatabase
            #
            # This script was developed to work with ArcGIS 10 and Python 2.6 installed during ArcGIS installation. 
            #
            # ------------------------------------------------------------------------------------------------------
            
            # Import arcpy module 
            try:
                import arcpy
                
            except:
                print ("Error importing arcpy module")
                print arcpy.GetMessages()
                
            print "arcpy successfully imported"
            
            # Setting a boolean statement.  NOTE: The default is set to True so that it will run as a tool within ArcGIS.  
            # To run the script outside of ArcGIS, change to False in the next line of code
            RunningWithArcGISGUI = (True)
            
            try: 
                
            # if the script is running within ArcGIS as a tool, get the following user defined parameters:  
                if (RunningWithArcGISGUI) == (True): 
                    
                    # The input file in the SRDG.csv file format
                    Parameter1 = parameters[0].valueAsText
                    
                    # A temporary XY Layer needed to create the feature class. 
                    # NOTE: This file is deleted automatically when the script finishes
                    Parameter2 = "TempXYLayer"                   
                    
                    # The spatial reference for the data (i.e. GCS_WGS84)
                    # XXX? how to get this quicker? CAN WE USE THE AUTOFEATURE FOR THIS?
                    Parameter3 = parameters[1].valueAsText   
                  
                    # The location of the File Geodatabase that will be created
                    Parameter4 = parameters[2].valueAsText     
                    
                    # The name of the File Geodatabase
                    Parameter5 = parameters[3].valueAsText  
                 
                    # The name of the Output Feature Class that will be created
                    Parameter6 = parameters[4].valueAsText     
                    
            # if the script is NOT running within ArcGIS as a tool, please define the following parameters by hard coding all the inputs below EXCEPT Parameter2
                else:
                    # The input file in the SRDG.csv file format
                    Parameter1 = "C:\\geneGIS\\WorkingFolder\\SRGD_Photo_GeneSPLASH_CentAM_CA_OR_Feb12_v3.csv"     
                    
                    # The temporary XY Layer required to create the feature class.  
                    # NOTE: DO NOT change this line of code!
                    Parameter2 = "TempXYLayer"                                         
                    
                    # The spatial reference for the data (i.e. GCS_WGS84)
                    Parameter3 = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119521E-09;0.001;0.001;IsHighPrecision"
                    
                    # The location of the File Geodatabase that will be created
                    Parameter4 = "C:\\geneGIS\\WorkingFolder"
                    
                    # The name of the File Geodatabase
                    Parameter5 = "PG_SPLASH_Subset2" 
                    
                    # The name of the Output Feature Class that will be created
                    Parameter6 = "TestFC"
            
            except:
                print ("Error setting tool parameters")
                print arcpy.GetMessages()
                    
            print "Parameters successfully defined"
                
            
            try:
                # XXX: SELECT COLUMNS VS hardcoded? perhaps just handle case better.
            
                # Process: Make XY Event Layer.  This layer is temporary and will be deleted upon script completion.
                # SYNTAX: arcpy.MakeXYEventLayer_management(table, in_x_field, in_y_field, out_layer, {spatial_reference}, {in_z_field})
                arcpy.MakeXYEventLayer_management(Parameter1, "Longitude", "Latitude", Parameter2, Parameter3, "")
            
            except:
                print ("Error making XY Event Layer")
                print arcpy.GetMessages()
                        
            print ("XY event layer successfully created")
            
            
            try:
                
                # Process: Create File GDB
                # SYNTAX: CreateFileGDB_management (out_folder_path, out_name, {out_version})
                arcpy.CreateFileGDB_management(Parameter4, Parameter5, "CURRENT")
            
            except:
                print ("Error creating File GDB")
                print arcpy.GetMessages()    
                
            print "File GDB successfully created"
            
            try:
                # XXX: this just copies everything, need more validation.
                # XXX: haplotypes? Alphanumeric code A1 A2 A+
                # PROBABLY DUMP THIS, use our OWN importer... so 
                # Deal with Date and times! problematic still.
                # CAN WE interface with MGET here?
            
                # 'Blanks in the haplotypes? code them this way.'
                # LOTS of conversion software already exists
                # CAN WE READ IN A STANDARD FORMAT?
            
            
                # Process: Copy Features
                # SYNTAX: CopyFeatures_management (in_features, out_feature_class, {config_keyword}, {spatial_grid_1}, {spatial_grid_2}, {spatial_grid_3})
                arcpy.CopyFeatures_management(Parameter2, Parameter4 + '\\' + Parameter5 + '.gdb\\' + Parameter6, "", "0", "0", "0")
            
            except:
                print ("Error copying features to a feature class")
                print arcpy.GetMessages() 
                
            print "Feature Class successfully created"
            
            print "Step 1 is done!"
            
class classifiedimport(object):
    """C:\data\arcgis\toolboxes\geneGIS_29July2012\geneGIS_29July2012.tbx\csvtofeatureclass"""
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
        print "parameters updated..."
        return
    
      def updateMessages(self):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return
    
    def __init__(self):
        self.label = u'CSV Classified Import'
        self.description = u'This tool allows the user to covert an input file (formated with the SRGD.csv specifications) to a feature class within a file geodatabse.'
        self.canRunInBackground = False

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
        gdb_loc= arcpy.Parameter()
        gdb_loc.name = u'File_Geodatabase_Location'
        gdb_loc.displayName = u'File Geodatabase Location'
        gdb_loc.parameterType = 'Required'
        gdb_loc.direction = 'Input'
        gdb_loc.datatype = u'Folder'

        # File_Geodatabase_Name
        gdb_label = arcpy.Parameter()
        gdb_label.name = u'File_Geodatabase_Name'
        gdb_label.displayName = u'File Geodatabase Name'
        gdb_label.parameterType = 'Required'
        gdb_label.direction = 'Input'
        gdb_label.datatype = u'String'

        # Output_Feature_Class
        output_fc= arcpy.Parameter()
        output_fc.name = u'Output_Feature_Class'
        output_fc.displayName = u'Output Feature Class'
        output_fc.parameterType = 'Required'
        output_fc.direction = 'Input'
        output_fc.datatype = u'String'

        # genetic columns
        genetics = arcpy.Parameter()
        genetics.name = u'Genetic_Columns'
        genetics.displayName = u'Genetic Columns'
        genetics.parameterType = 'Required'
        genetics.direction = 'Input'
        genetics.multiValue = True
        genetics.filter.list = ['locus1_A1', 'locus1_A2']

        # identification columns
        identification = arcpy.Parameter()
        identification.name = 'Identification_Columns'
        identification.displayName = 'Identification Columns'
        identification.parameterType = 'Required'
        identification.direction = 'Input'
        identification.multiValue = True
        identification.filter.list = ['Individual ID', 'Other ID']

        # location columns
        loc = arcpy.Parameter()
        loc.name = u'Location_Columns'
        loc.displayName = u'Location Columns'
        loc.parameterType = 'Required'
        loc.direction = 'Input'
        loc.multiValue = True
        loc.filter.list = ['latitude', 'longitude']

       # other columns
        other = arcpy.Parameter()
        other.name = u'Other_Columns'
        other.displayName = u'Other Columns'
        other.parameterType = 'Optional'
        other.direction = 'Input'
        other.multiValue = True
        other.filter.list = ['other A', 'other B']

        return [input_csv, sr, gdb_loc, gdb_label, output_fc, genetics, identification, loc, other]

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

        # perform some dynamic list filtering, in the case that we have a 
        # CSV input selected.
        cols = {'input_csv': 0,
                'sr': 1,
                'gdb_loc': 2,
                'gdb_label': 3,
                'output_fc': 4,
                'Genetic': 5,
                'Identification': 6,
                'Location': 7,
                'Other': 8
        }
        dynamic_cols = ['Genetic', 'Identification', 'Location', 'Other']
        unused_values = []

        if parameters[cols['input_csv']] is not None:
            # FIXME: handle other file formats than just a CSV with 
            # commas (see fancy import addin)

            # read the CSV header
            input_csv = csv.reader(open(parameters[cols['input_csv']].valueAsText, 'r'), delimiter=',')

            # pull off the first line of the CSV
            header = input_csv.next()
            unused_values = header
            
            # try modifying our first attribute columns list
            parameters[cols['Genetic']].filter.list = unused_values

        # select each set of columns and filter dependent lists
        for i, label in enumerate(dynamic_cols[1:]):
            update_label = cols[label]
            filter_label= cols[dynamic_cols[i]]
            #f.write("Running with: {0} {1} {2}\n\n".format(update_label,
            #    filter_label, ",".join(unused_values)))
            unused_values = self.updateDynamicFilters(
                    parameters[filter_label], 
                    parameters[update_label], 
                    unused_values)

        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):

        try: 
            # The input file in the SRDG.csv file format
            Parameter1 = parameters[0].valueAsText
                    
            # A temporary XY Layer needed to create the feature class. 
            # NOTE: This file is deleted automatically when the script finishes
            Parameter2 = "TempXYLayer"                   
                    
            # The spatial reference for the data (i.e. GCS_WGS84)
            # XXX? how to get this quicker? CAN WE USE THE AUTOFEATURE FOR THIS?
            Parameter3 = parameters[1].valueAsText   
                  
            # The location of the File Geodatabase that will be created
            Parameter4 = parameters[2].valueAsText     
                    
            # The name of the File Geodatabase
            Parameter5 = parameters[3].valueAsText  
            
            # The name of the Output Feature Class that will be created
            Parameter6 = parameters[4].valueAsText     
                    
           
        except:
            print ("Error setting tool parameters")
            print arcpy.GetMessages()
                    
        print "Parameters successfully defined"
                
            
        try:
            # XXX: SELECT COLUMNS VS hardcoded? perhaps just handle case better.
            
            # Process: Make XY Event Layer.  This layer is temporary and will be deleted upon script completion.
            # SYNTAX: arcpy.MakeXYEventLayer_management(table, in_x_field, in_y_field, out_layer, {spatial_reference}, {in_z_field})
            arcpy.MakeXYEventLayer_management(Parameter1, "Longitude", "Latitude", Parameter2, Parameter3, "")
            
        except:
            print ("Error making XY Event Layer")
            print arcpy.GetMessages()
                        
        print ("XY event layer successfully created")
            
            
        try:
            # Process: Create File GDB
            # SYNTAX: CreateFileGDB_management (out_folder_path, out_name, {out_version})
            arcpy.CreateFileGDB_management(Parameter4, Parameter5, "CURRENT")
            
        except:
            print ("Error creating File GDB")
            print arcpy.GetMessages()    
                
        print "File GDB successfully created"
            
        try:
            # XXX: this just copies everything, need more validation.
            # XXX: haplotypes? Alphanumeric code A1 A2 A+
            # PROBABLY DUMP THIS, use our OWN importer... so 
            # Deal with Date and times! problematic still.
            # CAN WE interface with MGET here?
            
            # 'Blanks in the haplotypes? code them this way.'
            # LOTS of conversion software already exists
            # CAN WE READ IN A STANDARD FORMAT?
            
            # Process: Copy Features
            # SYNTAX: CopyFeatures_management (in_features, out_feature_class, {config_keyword}, {spatial_grid_1}, {spatial_grid_2}, {spatial_grid_3})
            arcpy.CopyFeatures_management(Parameter2, Parameter4 + '\\' + Parameter5 + '.gdb\\' + Parameter6, "", "0", "0", "0")
            
        except:
            print ("Error copying features to a feature class")
            print arcpy.GetMessages() 
                
        print "Feature Class successfully created"
            
        print "Step 1 is done!"

class ExportGenAlex2(object):
    """C:\data\arcgis\toolboxes\geneGIS_29July2012\geneGIS_29July2012.tbx\ExportGenAlex2"""
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
        param_1 = arcpy.Parameter()
        param_1.name = u'Input_Feature_Class'
        param_1.displayName = u'Input Feature Class'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Feature Layer'

        # Where_Clause
        param_2 = arcpy.Parameter()
        param_2.name = u'Where_Clause'
        param_2.displayName = u'Where Clause'
        param_2.parameterType = 'Optional'
        param_2.direction = 'Input'
        param_2.datatype = u'SQL Expression'

        # Attribute_Field__to_order_by_population_
        param_3 = arcpy.Parameter()
        param_3.name = u'Attribute_Field__to_order_by_population_'
        param_3.displayName = u'Attribute Field (to order by population)'
        param_3.parameterType = 'Optional'
        param_3.direction = 'Input'
        param_3.datatype = u'Field'

        # Output_File_Location
        param_4 = arcpy.Parameter()
        param_4.name = u'Output_File_Location'
        param_4.displayName = u'Output File Location'
        param_4.parameterType = 'Required'
        param_4.direction = 'Input'
        param_4.datatype = u'Folder'

        # Output_File_Name
        param_5 = arcpy.Parameter()
        param_5.name = u'Output_File_Name'
        param_5.displayName = u'Output File Name'
        param_5.parameterType = 'Required'
        param_5.direction = 'Input'
        param_5.datatype = u'String'

        return [param_1, param_2, param_3, param_4, param_5]
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
        with script_run_as(u'C:\\data\\arcgis\\toolboxes\\geneGIS_29July2012\\Scripts\\ExportToGenAlEx_CodominantData.py'):
            # ------------------------------------------------------------------------------------------------------
            # ExportToGenAlEx_CodominantData.py
            #
            # Created by: Dori Dick
            #             College of Earth, Ocean and Atmospheric Sciences
            #             Oregon State Univeristy
            #
            # Created on: 19 March 2012
            # Last modified: 28 July 2012
            # 
            # Description: This script exports a feature class containing spatially referenced genetic into the text 
            #              file format required by GenAlEx (Peakall and Smouse 2006), an MS Excel Add-In created to run
            #              various genetic analyses in Excel.  
            #              GenAlEx is available from the following website: http://www.anu.edu.au/BoZo/GenAlEx/
            #
            # Required Inputs: An existing Feature Class containing spatially referenced genetic data for additional 
            #                  analysis in GenAlEx
            #
            # Optional Inputs: A Where Clause option using a SQL Expression to identify only those rows with genetic data in the Feature Class.  
            #                          NOTE: This parameter is optional and was included because some data sets may have individual IDs 
            #                          based on more than just genetics (i.e. photo-id).  
            #
            #                          An Attribute Field that distinguishes the populations in the Input Feature Class.
            #                          NOTE: This parameter is optional and was included because some data sets may have 
            #                          more than one population in it.  
            #
            # Script Outputs: A comma delimited text file formated to match the required input for GenAlEx
            #              
            # This script was developed to work with ArcGIS 10 and Python 2.6 installed during ArcGIS installation. 
            #
            # ------------------------------------------------------------------------------------------------------
            
            # Import arcpy module
            try:
                import arcpy
            
            except:
                print ("Error importing arcpy module")
                print arcpy.GetMessages()
                
            print "arcpy successfully imported"
            
            # Setting a boolean statement.  NOTE: The default is set to True so that it will run as a tool within ArcGIS.  
            # To run the script outside of ArcGIS, change to False in the next line of code
            RunningWithArcGISGUI = (True)
            
            try:
                
            # if the script is running within ArcGIS as a tool, get the following user defined parameters: 
                if (RunningWithArcGISGUI) == (True):
                    
                    # The Input Feature Class
                    Parameter1 = parameters[0].valueAsText 
                    
                    # Where clause that can be used to pull out only those rows with genetic data from the feature class 
                    # NOTE: This parameter is optional and was included because some data sets may have individual IDs based on 
                    # more than just genetics (i.e. photo-id).  If your data only has genetic records, this parameter can be left
                    # blank
                    Parameter2 = parameters[1].valueAsText        
            
                    # The Attribute Field that distinguishes the populations in the Input Feature Class.
                    # NOTE: This parameter is optional and was included because some data sets may have more than one population
                    # in it. 
                    Parameter3 = parameters[2].valueAsText
            
                    # The Output File location
                    Parameter4 = parameters[3].valueAsText    
                    
                    # The Output Text File Name
                    Parameter5 = parameters[4].valueAsText          
                  
            # if the script is NOT running within ArcGIS as a tool, please define the following parameters by hard coding all 
            # the inputs below   
                else:
                    # The Input Feature Class
                    Parameter1 = "C:\\geneGIS\\WorkingFolder\\test_20March.gdb\\SPLASH_Whales"    
                    
                    # The attribute field and Where Clause required to pull out only those rows with genetic data from the feature class.  
                    # NOTE: This parameter is optional and was included because some data sets may have individual IDs based on 
                    # more than just genetics (i.e. photo-id).  If your data only has genetic records, this parameter can be left
                    # blank 
                    Parameter2 = "OtherID_1" + "<>'" + str("")+"'"
                                 
                    # The Attribute Field that distinguishes the populations in the Input Feature Class.
                    # NOTE: This parameter is optional and was included becasue some data sets may have more than one population
                    # in it. 
                    Parameter3 = "Area"
                  
                    # The  Output File location
                    Parameter4 = "C:\\geneGIS\\WorkingFolder"
                    
                    # The Output Text File Name
                    Parameter5 = "GenAlex_ExportTest2"                
            
            except:
                print ("Error setting tool parameters")
                print arcpy.GetMessages()
                    
            print "Parameters successfully defined"
            
            try:    
            
                # Create and open the Output comma separated text file to which the data will be written
                OutputFile = open(Parameter4 + "\\" + Parameter5 + ".txt", "w")
            
            except:
                print "Unable to open text file"
                
            print "Output file open and ready for data input"
                    
            try: 
             
                # Creating the GenAlEx header information required for the text file. NOTE: This includes 2 blank rows followed by the data
                OutputFile.write("\n")     
                OutputFile.write("\n")
                OutputFile.write("Individual_ID" + "," + Parameter3 + "," + "Locus1_A1" + "," + "" + "," +\
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
                rows = arcpy.SearchCursor(Parameter1)
                rows = arcpy.SearchCursor(Parameter1, Parameter2, "", "", Parameter3 + " A")
                row = rows.next()
                
                # A while loop used to move through each row of data and pull the value for each of the necessary fields
                while row:     
                    OutputFile.write(str(row.Individual_ID) + "," + str(row.getValue(Parameter3))+ "," + str(row.Locus1_A1) + "," + str(row.Locus1_A2) + "," +\
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
            
            
            
            
            

class ExportGenAlex3(object):
    """C:\data\arcgis\toolboxes\geneGIS_29July2012\geneGIS_29July2012.tbx\ExportGenAlex3"""
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
        self.label = u'Export to GenAlex_HaploidData'
        self.description = u'This tool allows the user to export data to a comma separated text file that follows the required input format for GenAlEx (Peakall and Smouse 2006), a Microsoft Excel Add-In.\r\n\r\nGenAlEx is available from:\r\n\r\nhttp://www.anu.edu.au/BoZo/GenAlEx/\r\n'
        self.canRunInBackground = False
    def getParameterInfo(self):
        # Input_Feature_Class
        param_1 = arcpy.Parameter()
        param_1.name = u'Input_Feature_Class'
        param_1.displayName = u'Input Feature Class'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Feature Layer'

        # Where_Clause
        param_2 = arcpy.Parameter()
        param_2.name = u'Where_Clause'
        param_2.displayName = u'Where Clause'
        param_2.parameterType = 'Optional'
        param_2.direction = 'Input'
        param_2.datatype = u'SQL Expression'

        # Attribute_Field__to_order_by_population_
        param_3 = arcpy.Parameter()
        param_3.name = u'Attribute_Field__to_order_by_population_'
        param_3.displayName = u'Attribute Field (to order by population)'
        param_3.parameterType = 'Optional'
        param_3.direction = 'Input'
        param_3.datatype = u'Field'

        # Output_File_Location
        param_4 = arcpy.Parameter()
        param_4.name = u'Output_File_Location'
        param_4.displayName = u'Output File Location'
        param_4.parameterType = 'Required'
        param_4.direction = 'Input'
        param_4.datatype = u'Folder'

        # Output_File_Name
        param_5 = arcpy.Parameter()
        param_5.name = u'Output_File_Name'
        param_5.displayName = u'Output File Name'
        param_5.parameterType = 'Required'
        param_5.direction = 'Input'
        param_5.datatype = u'String'

        return [param_1, param_2, param_3, param_4, param_5]
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
        with script_run_as(u'C:\\data\\arcgis\\toolboxes\\geneGIS_29July2012\\Scripts\\ExportToGenAlEx_HaploidData.py'):
            # ------------------------------------------------------------------------------------------------------
            # ExportToGenAlEx_HaploidData.py
            #
            # Created by: Dori Dick
            #             College of Earth, Ocean and Atmospheric Sciences
            #             Oregon State Univeristy
            #
            # Created on: 19 March 2012
            # Last modified: 28 July 2012
            # 
            # Description: This script exports a feature class containing spatially referenced genetic into the text 
            #              file format required by GenAlEx (Peakall and Smouse 2006), an MS Excel Add-In created to run
            #              various genetic analyses in Excel.  
            #              GenAlEx is available from the following website: http://www.anu.edu.au/BoZo/GenAlEx/
            #
            # Required Inputs: An existing Feature Class containing spatially referenced genetic data for additional 
            #                  analysis in GenAlEx
            #
            # Optional Inputs: A Where Clause option using a SQL Expression to identify only those rows with genetic data in the Feature Class.  
            #                          NOTE: This parameter is optional and was included because some data sets may have individual IDs 
            #                          based on more than just genetics (i.e. photo-id).  
            #
            #                          An Attribute Field that distinguishes the populations in the Input Feature Class.
            #                          NOTE: This parameter is optional and was included because some data sets may have 
            #                          more than one population in it.  
            #
            # Script Outputs: A comma delimited text file formated to match the required input for GenAlEx
            #              
            # This script was developed to work with ArcGIS 10 and Python 2.6 installed during ArcGIS installation. 
            #
            # ------------------------------------------------------------------------------------------------------
            
            # Import arcpy module
            try:
                import arcpy
            
            except:
                print ("Error importing arcpy module")
                print arcpy.GetMessages()
                
            print "arcpy successfully imported"
            
            # Setting a boolean statement.  NOTE: The default is set to True so that it will run as a tool within ArcGIS.  
            # To run the script outside of ArcGIS, change to False in the next line of code
            RunningWithArcGISGUI = (True)
            
            try:
                
            # if the script is running within ArcGIS as a tool, get the following user defined parameters: 
                if (RunningWithArcGISGUI) == (True):
                    
                    # The Input Feature Class
                    Parameter1 = parameters[0].valueAsText 
                    
                    # Where clause that can be used to pull out only those rows with genetic data from the feature class 
                    # NOTE: This parameter is optional and was included because some data sets may have individual IDs based on 
                    # more than just genetics (i.e. photo-id).  If your data only has genetic records, this parameter can be left
                    # blank
                    Parameter2 = parameters[1].valueAsText        
            
                    # The Attribute Field that distinguishes the populations in the Input Feature Class.
                    # NOTE: This parameter is optional and was included because some data sets may have more than one population
                    # in it. 
                    Parameter3 = parameters[2].valueAsText
            
                    # The Output File location
                    Parameter4 = parameters[3].valueAsText    
                    
                    # The Output Text File Name
                    Parameter5 = parameters[4].valueAsText          
                  
            # if the script is NOT running within ArcGIS as a tool, please define the following parameters by hard coding all 
            # the inputs below   
                else:
                    # The Input Feature Class
                    Parameter1 = "C:\\geneGIS\\WorkingFolder\\test_20March.gdb\\SPLASH_Whales"    
                    
                    # The attribute field and Where Clause required to pull out only those rows with genetic data from the feature class.  
                    # NOTE: This parameter is optional and was included because some data sets may have individual IDs based on 
                    # more than just genetics (i.e. photo-id).  If your data only has genetic records, this parameter can be left
                    # blank 
                    Parameter2 = "OtherID_1" + "<>'" + str("")+"'"
                                 
                    # The Attribute Field that distinguishes the populations in the Input Feature Class.
                    # NOTE: This parameter is optional and was included becasue some data sets may have more than one population
                    # in it. 
                    Parameter3 = "Area"
                  
                    # The  Output File location
                    Parameter4 = "C:\\geneGIS\\WorkingFolder"
                    
                    # The Output Text File Name
                    Parameter5 = "GenAlex_ExportTest2"                
            
            except:
                print ("Error setting tool parameters")
                print arcpy.GetMessages()
                    
            print "Parameters successfully defined"
            
            try:    
            
                # Create and open the Output comma separated text file to which the data will be written
                OutputFile = open(Parameter4 + "\\" + Parameter5 + ".txt", "w")
            
            except:
                print "Unable to open text file"
                
            print "Output file open and ready for data input"
                    
            try: 
             
                # Creating the GenAlEx header information required for the text file. NOTE: This includes 2 blank rows followed by the data
                OutputFile.write("\n")     
                OutputFile.write("\n")
                OutputFile.write("Individual_ID" + "," + Parameter3 + "," + "Haplotype" + "," + "" + "," + "Latitude" + "," + "Longitude" + "\n") 
                
            except:
                print "Unable to write header info to text file"
                
            print "Header info written to text file"
            
            try:
                
                # Creating a search cursor that will move through the input feature class, row by row
                # Note the WhereClause: Because the SPLASH data has both photo-id and genetic records, but GenAlEx only uses genetic data, the 
                #                       WhereClause is used to ensure only those records with genetic data are copied to the text file. 
                rows = arcpy.SearchCursor(Parameter1)
                rows = arcpy.SearchCursor(Parameter1, Parameter2, "", "", Parameter3 + " A")
                row = rows.next()
                
                # A while loop used to move through each row of data and pull the value for each of the necessary fields
                while row:     
                    OutputFile.write(str(row.Individual_ID) + "," + str(row.getValue(Parameter3))+ "," + str(row.Haplotype) + "," + "" + "," + str(row.Latitude) + "," + str(row.Longitude) + "\n")
                    row = rows.next()
            
            except:
                print "Unable to write data to text file"
            
            print "Data written to text file"
            
            # Close Output text file
            OutputFile.close()
            
            print "Done!"
            
            
            
            
            

class SelectDataByAttributes(object):
    """C:\data\arcgis\toolboxes\geneGIS_29July2012\geneGIS_29July2012.tbx\SelectDataByAttributes"""
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
            
