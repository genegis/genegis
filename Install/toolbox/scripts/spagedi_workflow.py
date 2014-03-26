#!/usr/bin/env python
"""
Standalone script to test drive spagedi functionality.
"""
import os, re, sys, time, platform, glob, getopt
from random import randint
import argparse as ap
import xml.etree.cElementTree as et
from pprint import pprint as pp
from usage import Usage
import arcpy
from functools import wraps
from spagedi_tree import *

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
                    "Error in task \"" + task + "\" (" + sys.exc_info()[0].__name__ + "/" +
                    fname + "/" + str(exc_tb.tb_lineno) + "):\n--> " + e.message
                )
                with open(self.log, 'a') as logfile:
                    print >>logfile, erroroutput + "\nTraceback:"
                    traceback.print_tb(exc_tb, limit=5, file=logfile)
        return wrapper
    return decorate

class BoxOfSpagedi(object):
    """
    BoxOfSpagedi: a conveniently shaped object from which you can
    tools of Spagedi, without ever leaving the comfort of Python.
    """
    TREE = spagedi_tree()

    def __init__(self, standalone=True, sequence=None, input_fc=None,
                 output_file=None, order_by=None, analysis_type=None):
        self.label = u'Genetic Analysis - F_st'
        self.description = u'Calculate F_st using Jacknifing'
        self.canRunInBackground = False
        self.category = "Analysis"
        self.cols = {
            'input_fc': 0,
            'order_by': 1,
            'analysis_type': 2,
            'output_file': 3
        }
        self.standalone = standalone
        self.sequence = sequence
        self.input_fc = input_fc
        self.output_file = output_file
        self.order_by = order_by
        self.analysis_type = analysis_type

    def getParameterInfo(self):

        # Input Feature Class
        if self.standalone:
            input_fc = {}
            input_fc['name'] = u'Input_Feature_Class'
            input_fc['displayName'] = u'Feature Class'
            input_fc['direction'] = 'Input'
            input_fc['parameterType'] = 'Required'
            input_fc['datatype'] = dt.format('Feature Layer')
            input_fc['valueAsText'] = self.input_fc
            input_fc = ap.Namespace(**input_fc)
            
            order_by = {}
            order_by['name'] = u'Population Field'
            order_by['displayName'] = u'Population Field'
            order_by['parameterType'] = 'Required'
            order_by['direction'] = 'Input'
            order_by['datatype'] = dt.format('Field')
            order_by['parameterDependencies'] = [input_fc.name]
            order_by['valueAsText'] = self.order_by
            order_by = ap.Namespace(**order_by)

            analysis_type = {}
            analysis_type['name'] = 'Analysis_Type'
            analysis_type['displayName'] = 'Analysis Type'
            analysis_type['direction'] = 'Input'
            analysis_type['parameterType'] = 'Required'
            analysis_type['datatype'] = dt.format('String')
            analysis_type['filter.list'] = ['Jacknifing']
            analysis_type['valueAsText'] = self.analysis_type
            analysis_type = ap.Namespace(**analysis_type)

            output_file = {}
            output_file['name'] = u'Output_File'
            output_file['displayName'] = u'Output Results File'
            output_file['direction'] = 'Output'
            output_file['parameterType'] = 'Required'
            output_file['datatype'] = dt.format('File')
            output_file['valueAsText'] = self.output_file
            output_file = ap.Namespace(**output_file)
        else:
            input_fc = arcpy.Parameter()
            input_fc.name = u'Input_Feature_Class'
            input_fc.displayName = u'Feature Class'
            input_fc.direction = 'Input'
            input_fc.parameterType = 'Required'
            input_fc.datatype = dt.format('Feature Layer')

            # Attribute_Field__to_order_by_population_
            order_by = arcpy.Parameter()
            order_by.name = u'Population Field'
            order_by.displayName = u'Population Field'
            order_by.parameterType = 'Required'
            order_by.direction = 'Input'
            order_by.datatype = dt.format('Field')
            order_by.parameterDependencies=[input_fc.name]

            # Analysis Type
            analysis_type = arcpy.Parameter()
            analysis_type.name = 'Analysis_Type'
            analysis_type.displayName = 'Analysis Type'
            analysis_type.direction = 'Input'
            analysis_type.parameterType = 'Required'
            analysis_type.datatype = dt.format('String')
            analysis_type.filter.list = ['Jacknifing']
            analysis_type.value = 'Jacknifing'

            # Output File
            output_file = arcpy.Parameter()
            output_file.name = u'Output_File'
            output_file.displayName = u'Output Results File'
            output_file.direction = 'Output'
            output_file.parameterType = 'Required'
            output_file.datatype = dt.format('File')

        return [input_fc, order_by, analysis_type, output_file]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        output_file = parameters[self.cols['output_file']]
        output_file.value = utils.set_file_extension(output_file, 'txt')
        return

    def updateMessages(self, parameters):
        return

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

{sequence_0}
{sequence_1}
{sequence_2}



""".format(spagedi_file_path=spagedi_file_path,
           results=results,
           sequence_0=self.sequence[0],
           sequence_1=self.sequence[1],
           sequence_2=self.sequence[2])
            print file_string
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

        cmd = "{spagedi_exe} < {spagedi_commands}".format(
                spagedi_exe=spagedi_executable_path,
                spagedi_commands=spagedi_commands)
        utils.msg("trying to run %s" % cmd)

        # TODO replace with subprocess call
        res = os.system(cmd)

        utils.msg("trying to open resulting file %s" % results)
        os.startfile(results)
        utils.msg("all done!")


def prepare(sauce):
    if os.path.isfile(sauce['output_file']):
        os.remove(sauce['output_file'])
    scriptloc = os.path.dirname(os.path.realpath(__file__))
    mxdpath = os.path.abspath(os.path.join(scriptloc, os.path.pardir, 'genegis.mxd'))
    mxd = arcpy.mapping.MapDocument(mxdpath)
    for lyr in arcpy.mapping.ListLayers(mxd):
        if lyr.name == 'SRGD_example_Spatial':
            arcpy.CopyFeatures_management(lyr, sauce['input_fc'])
            return

def descend(T, sequence, randomize=False):
    print T.pop('headline')
    for key, item in sorted(T.items()):
        print key + '.', item.label
    while True:
        selection = str(randint(0, len(T))) if randomize else raw_input("Selection: ")
        if selection in T.keys():
            break
    sequence.append(selection)
    if 'next' in item:
        descend(T[sequence[-1]].next, sequence, randomize)
    return sequence

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], 'hr', ['help', 'random'])
        except getopt.GetoptError as e:
             raise Usage(e)
        input_fc = "in_memory/temp"
        output_file = r"C:\Users\Sparky\src\genegis\tests\data\test_spagedi_export.txt"
        randomize = False
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                print __doc__
                return 0
            elif opt in ('-r', '--random'):
                randomize = True
        
        # Prompt the user: what test are we doing?
        sequence = descend(BoxOfSpagedi.TREE, [], randomize)
        analysis_type = BoxOfSpagedi.TREE[sequence[0]].next[sequence[1]].next[sequence[2]].label
        sauce = {
            'standalone': True,
            'sequence': sequence,
            'input_fc': input_fc,
            'output_file': output_file,
            'analysis_type': analysis_type,
            'order_by': 'Individual_ID',
        }
        pp(sauce)

        # Clear out any leftover outputs from previous runs and
        # get the input feature class loaded into memory
        prepare(sauce)

        # Fire up Spagedi and crunch some numbers
        spagedi = BoxOfSpagedi(**sauce)
        parameters = spagedi.getParameterInfo()
        spagedi.execute(parameters, None)

    except Usage as e:
        print >>sys.stderr, e.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__=='__main__':
    sys.exit(main())
