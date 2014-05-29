#!/usr/bin/env python
"""
Standalone script to test drive spagedi functionality.
"""
import os, re, sys, time, platform, glob, getopt, traceback
from functools import wraps
import xml.etree.cElementTree as et
from usage import Usage
import arcpy
from spagedi_tree import spagedi_tree
# enable local imports; allow importing both this directory and one above
import add_install_path
from bunch import Bunch

# addin specific configuration and utility functions
import utils as addin_utils
import config

# import utilities & config from our scripts as well
from scripts import utils

# import our datatype conversion submodule
from datatype import datatype
dt = datatype.DataType()

def error_handler(task=""):
    def decorate(task_func):
        @wraps(task_func)
        def wrapper(self, *args, **kwargs):
            try:
                return task_func(self, *args, **kwargs)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                erroroutput = (
                    "Error in task \"" + task + "\" (" +
                    fname + "/" + str(exc_tb.tb_lineno) + "):\n--> " + e.message
                )
                with open(self.log, 'a') as logfile:
                    print >>logfile, erroroutput + "\nTraceback:"
                    traceback.print_tb(exc_tb, limit=5, file=logfile)
        return wrapper
    return decorate

class SpagediWrapper(object):
    """
    Wrapper for the SPAGeDi command line tool for spatial pattern analysis
    of genetic diversity.  This script is tested on SPAGeDi 1.4a, running
    on Windows 7, with ArcGIS 10.2.
    """
    def __init__(self, standalone=True, sequence=None, input_fc=None,
                 output_file=None, order_by=None, analysis_type=None,
                 spagedi_file_path=None, show_spagedi_output=False):
        self.sequence = sequence
        self.label = self.sequence[1]
        self.description = self.sequence[3]
        self.spagedi_file_path = spagedi_file_path
        self.show_spagedi_output = show_spagedi_output
        self.canRunInBackground = False
        self.category = "Analysis"
        self.cols = {
            'input_fc': 0,
            'order_by': 1,
            'analysis_type': 2,
            'output_file': 3
        }
        self.standalone = standalone
        self.input_fc = input_fc
        self.output_file = output_file
        self.order_by = order_by
        self.analysis_type = analysis_type
        self.log = 'log/error.log'

    @error_handler("getParameterInfo")
    def getParameterInfo(self):

        # Bunch has attribute-style access, so it is a reasonable
        # substitute for arcpy's Parameter class
        if self.standalone:
            input_fc = Bunch()
            order_by = Bunch()
            analysis_type = Bunch()
            analysis_type.filter = Bunch()
            output_file = Bunch()
            input_fc.valueAsText = self.input_fc
            order_by.valueAsText = self.order_by
            analysis_type.valueAsText = self.analysis_type
            output_file.valueAsText = self.output_file
            
        else:
            input_fc = arcpy.Parameter()
            analysis_type = arcpy.Parameter()
            order_by = arcpy.Parameter()
            output_file = arcpy.Parameter()
            analysis_type.value = self.analysis_type

        # Input feature class
        input_fc.name = u'Input_Feature_Class'
        input_fc.displayName = u'Feature Class'
        input_fc.direction = 'Input'
        input_fc.parameterType = 'Required'
        input_fc.datatype = dt.format('Feature Layer')

        # Attribute_Field__to_order_by_population_    
        order_by.name = u'Population Field'
        order_by.displayName = u'Population Field'
        order_by.parameterType = 'Required'
        order_by.direction = 'Input'
        order_by.datatype = dt.format('Field')
        order_by.parameterDependencies=[input_fc.name]

        # Analysis Type           
        analysis_type.name = 'Analysis_Type'
        analysis_type.displayName = 'Analysis Type'
        analysis_type.direction = 'Input'
        analysis_type.parameterType = 'Required'
        analysis_type.datatype = dt.format('String')
        analysis_type.filter.list = [self.analysis_type]

        # Output File
        output_file.name = u'Output_File'
        output_file.displayName = u'Output Results File'
        output_file.direction = 'Output'
        output_file.parameterType = 'Required'
        output_file.datatype = dt.format('File')

        return [input_fc, order_by, analysis_type, output_file]

    def isLicensed(self):
        return True

    @error_handler("updateParameters")
    def updateParameters(self, parameters):
        output_file = parameters[self.cols['output_file']]
        output_file.value = utils.set_file_extension(output_file, 'txt')
        return

    def updateMessages(self, parameters):
        return

    @error_handler("execute")
    def execute(self, parameters, messages):
        from scripts import ExportToSPAGeDi
   
        results = parameters[3].valueAsText

        # temporary SPAGEDI output file
        if self.spagedi_file_path is not None:
            spagedi_file_path = self.spagedi_file_path
        else:
            spagedi_file_path = os.path.join(config.config_dir, "spagedi_data.txt")

        utils.msg("writing spagedi-formatted results...")

        # compute our spagedi file first
        ExportToSPAGeDi.main(
            input_features=parameters[0].valueAsText,
            where_clause="",
            order_by=parameters[1].valueAsText,
            output_name=spagedi_file_path
        )

        utils.msg("writing out spagedi commands...")

        # now, generate an input file for SPAGeDi
        spagedi_commands = os.path.join(config.config_dir, "spagedi_commands.txt")
        utils.msg(spagedi_commands)
        with open(spagedi_commands, 'w') as command_file:
            file_string = "{spagedi_file_path}\n{results}\n\n".format(
                spagedi_file_path=spagedi_file_path,
                results=results
            )
            for cmd in self.sequence:
                file_string += cmd + '\n'
            file_string += '\n\n\n'
            command_file.write(file_string)

        # now, fire up SPAGeDi
        spagedi_msg = """Now running SPAGeDi 1.4a (build 11-01-2013)
   - a program for Spatial Pattern Analysis of Genetic Diversity
               Written by Olivier Hardy & Xavier Vekemans
               Contributions by Reed Cartwright"""
        utils.msg(spagedi_msg)
        time.sleep(2)
        spagedi_executable_path = os.path.abspath( \
                os.path.join(os.path.abspath(os.path.dirname(__file__)), \
                "..", "lib", config.spagedi_executable))
        shell_cmd = "{spagedi_exe} < {spagedi_commands}".format(
                spagedi_exe=spagedi_executable_path,
                spagedi_commands=spagedi_commands)
        res = os.system(shell_cmd)
        return 0


def prepare(sauce):
    """
    Clear out any leftover outputs from previous runs and get the input
    feature class loaded into memory.
    """
    if os.path.isfile(sauce['output_file']):
        os.remove(sauce['output_file'])
    scriptloc = os.path.dirname(os.path.realpath(__file__))
    mxdpath = os.path.abspath(os.path.join(scriptloc, os.path.pardir, 'genegis.mxd'))
    mxd = arcpy.mapping.MapDocument(mxdpath)
    for lyr in arcpy.mapping.ListLayers(mxd):
        if lyr.name == 'SRGD_example_Spatial':
            arcpy.CopyFeatures_management(lyr, sauce['input_fc'])
            return sauce

def spagedi_user_inputs(T, sequence, defaults):
    """
    Prompt the user through Spagedi's decision tree, then save the commands so
    we can re-use them when we actually run Spagedi from the main workflow.
    """        
    print T.pop('headline')

    # Free-form user input
    if 'user_input' in T:
        for u in T.user_input:
            print u.label
            user_input = raw_input("> ")

            # Input can be path, number, or category
            # If it's a path, make sure the path exists
            if u.input_type == 'path':
                valid_path = False
                while not valid_path:
                    if not user_input or not os.path.exists(user_input):
                        if 'default' in u:
                            if u.default in defaults:
                                user_input = defaults[u.default]
                            else:
                                user_input = str(u.default)
                            valid_path = True
                        else:
                            print "Invalid path, try again"
                    else:
                        valid_path = True

            # If we're expecting a number, check to make sure the user
            # has entered a number
            elif u.input_type == 'number':
                is_number = False
                while not is_number:
                    if user_input:
                        try:
                            temp = float(user_input)
                            is_number = True
                        except TypeError as e:
                            print "Input must be a number, try again"
                    else:
                        if 'default' in u:
                            if u.default == -1:
                                user_input = ''
                            else:
                                if u.default in defaults:
                                    user_input = defaults[u.default]
                                else:
                                    user_input = str(u.default)
                            is_number = True

            sequence.append(user_input)
        return spagedi_user_inputs(T.next, sequence, defaults)

    # Prompt user to select an item from a menu
    else:
        options = sorted(T.items())
        for key, item in options:
            print key + '.', item.label
        skip = False
        complete = False
        while True:
            user_input = raw_input("Selection: ")
            if user_input in T:
                break

            # Retrofitted to allow users to press enter for the output
            # options and computational options layers
            # (this could be replaced with something less hackish)
            if not user_input and len(sequence) > 1:
                if '4' in T and 'label' in T['4']:
                    if T['4'].label == "jackknife over loci":
                        skip = True
                        user_input = '4'
                        break
                    elif len(T['4'].label) > 5 and T['4'].label[:6] == u"Report":
                        complete = True
                        user_input = ''
                        break
    
            print "Please select one of the options."
        sequence.append(user_input)
        if not complete:
            if sequence[-1] in T and 'next' in T[sequence[-1]]:

                # More "press enter" hackery
                if skip:
                    temp = sequence[-1]
                    sequence[-1] = ''
                    return spagedi_user_inputs(T[temp].next, sequence, defaults)

                return spagedi_user_inputs(T[sequence[-1]].next, sequence, defaults)
    return sequence

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], 'h', ['help'])
        except getopt.GetoptError as e:
             raise Usage(e)             
        input_fc = "in_memory/temp"
        output_file = os.path.join(config.config_dir, "test_spagedi_export.txt")
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                print __doc__
                return 0
        
        # Prompt the user: what test are we doing?
        defaults = Bunch({
            'spagedi_file_path': os.path.join(config.config_dir, "spagedi_data.txt"),
        })
        sequence = spagedi_user_inputs(spagedi_tree(), [], defaults)
        sauce = prepare({
            'standalone': True,
            'sequence': sequence,
            'input_fc': input_fc,
            'spagedi_file_path': defaults.spagedi_file_path,
            'output_file': output_file,
            'analysis_type': '',
            'order_by': 'Individual_ID',
            'show_spagedi_output': True,
        })

        # Fire up Spagedi and crunch some numbers
        spagedi = SpagediWrapper(**sauce)
        parameters = spagedi.getParameterInfo()
        return spagedi.execute(parameters, None)

    except Usage as e:
        print >>sys.stderr, e.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == '__main__':
    sys.exit(main())
