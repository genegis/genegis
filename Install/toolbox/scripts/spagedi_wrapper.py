#!/usr/bin/env python
"""
Standalone script to test drive spagedi functionality.
"""
import os, re, sys, time, platform, glob, getopt, traceback, subprocess
from functools import wraps
from random import randint
from collections import deque
import xml.etree.cElementTree as et
from pprint import pprint as pp
from usage import Usage
import arcpy
from spagedi_tree import spagedi_tree
from bunch import Bunch

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
    TREE = spagedi_tree()

    def __init__(self, standalone=True, sequence=None, input_fc=None,
                 output_file=None, order_by=None, analysis_type=None):
        self.sequence = sequence
        self.label = self.sequence[1]
        self.description = self.sequence[3]
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
            file_string = """{spagedi_file_path}
{results}
""".format(spagedi_file_path=spagedi_file_path, results=results)
            for cmd in self.sequence:
                file_string += cmd + '\n'
            file_string += '\n\n\n'
#             file_string = """{spagedi_file_path}
# {results}

# {sequence_0}
# {sequence_1}
# {sequence_2}
# {sequence_3}



# """.format(spagedi_file_path=spagedi_file_path,
#            results=results,
#            sequence_0=self.sequence[0],
#            sequence_1=self.sequence[1],
#            sequence_2=self.sequence[2],
#            sequence_3=self.sequence[3])
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

        p = subprocess.Popen([spagedi_executable_path], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        spagedi_output = p.communicate(input=file_string)[0]
        # print spagedi_output

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

def descend(T, sequence, randomize=False, grouping=None):
    """
    Prompt the user through Spagedi's decision tree, then save the commands so
    we can re-use them when we actually run Spagedi from the main workflow.
    """
    print T.keys()
    if 'population' in T and grouping is not None:
        print "descend(T[" + str(grouping) + "], " + str(sequence) + ", " + str(randomize) + ")"
        descend(T[grouping], sequence, randomize)
    else:
        if 'headline' in T:
            print T.pop('headline')
        if sequence:
            try:
                if 'user_input' in T[sequence[-1]]:
                    print "descend(T[" + str(sequence[-1]) + "], " + str(sequence) + ", " + str(randomize) + ")"
                    descend(T[sequence[-1]], sequence, randomize)
            except Exception as e:
                print e
                import ipdb; ipdb.set_trace()
        if 'user_input' in T:
            if 'label' in T.user_input:
                print T.user_input.label
            user_input = raw_input("> ")
            # Input can be path, number, or category
            if T.user_input.input_type == 'path':
                if not os.path.exists(user_input):
                    user_input = T.user_input.default
            elif T.user_input.input_type == 'number':
                is_number = False
                while not is_number:
                    try:
                        user_input = float(user_input)
                        is_number = True
                    except TypeError as e:
                        # if 'default' in T.user_input:
                        #     print "Invalid input, defaulting to", T.user_input.default
                        #     user_input = T.user_input.default
                        print "Input must be a number, try again"
        else:
            for key, item in sorted(T.items()):
                try:
                    print key + '.', item.label
                except AttributeError as e:
                    print e
                    import ipdb; ipdb.set_trace()
            while True:
                if randomize:
                    user_input = str(randint(0, len(T)))
                else:
                    user_input = raw_input("Selection: ")
                if user_input in T:
                    break
                print "Please select one of the options."
            if not sequence:
                grouping = 'individuals' if user_input == '1' else 'populations'
        sequence.append(user_input)
        if 'next' in item:
            print "descend(T[" + str(sequence[-1]) + "], " + str(sequence) + ", " + str(randomize) + ")"
            descend(T[sequence[-1]].next, sequence, randomize)
    return sequence

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], 'hrt', ['help', 'random', 'test'])
        except getopt.GetoptError as e:
             raise Usage(e)
        input_fc = "in_memory/temp"
        output_file = r"C:\Users\Sparky\src\genegis\tests\data\test_spagedi_export.txt"
        randomize = False
        testing = False
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                print __doc__
                return 0
            elif opt in ('-r', '--random'):
                randomize = True
            elif opt in ('-t', '--test'):
                testing = True

        # Prompt the user: what test are we doing?
        if not testing:
            sequence = descend(SpagediWrapper.TREE, [], randomize)
            analysis_type = SpagediWrapper.TREE[sequence[0]].next[sequence[1]].next[sequence[2]].label
        else:
            sequence = [1, 1, 1, 1]
            analysis_type = "testing"
        sauce = prepare({
            'standalone': True,
            'sequence': sequence,
            'input_fc': input_fc,
            'output_file': output_file,
            'analysis_type': analysis_type,
            'order_by': 'Individual_ID',
        })
        # print json.dumps(sauce, indent=3, sort_keys=True)

        # Fire up Spagedi and crunch some numbers
        spagedi = SpagediWrapper(**sauce)
        parameters = spagedi.getParameterInfo()
        return spagedi.execute(parameters, None)

    except Usage as e:
        print >>sys.stderr, e.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__=='__main__':
    sys.exit(main())
