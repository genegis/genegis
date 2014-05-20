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
from spagedi_tree import spagedi_tree, prp
from bunch import Bunch

# enable local imports; allow importing both this directory and one above
local_path = os.path.dirname(__file__)
for path in [local_path, os.path.join(local_path, '..')]:
    full_path = os.path.abspath(path)
    sys.path.insert(0, os.path.abspath(path))

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
        if 'user_input' in T:
            for u in T.user_input:
                if 'label' in u:
                    print u.label
                user_input = raw_input("> ")
                # Input can be path, number, or category
                if u.input_type == 'path':
                    if not os.path.exists(user_input):
                        user_input = u.default
                elif u.input_type == 'number':
                    is_number = False
                    while not is_number:
                        try:
                            user_input = float(user_input)
                            is_number = True
                        except TypeError as e:
                            print "Input must be a number, try again"
                sequence.append(user_input)
            print sequence
            descend(T.next, sequence, randomize)
        else:
            for key, item in sorted(T.items()):
                print key + '.', item.label
            while True:
                if randomize:
                    user_input = str(randint(0, len(T)))
                else:
                    user_input = raw_input("Selection: ")
                if user_input in T:
                    break
                print "Please select one of the options."
            if not sequence:
                grouping = 'individual' if user_input == '1' else 'population'
            sequence.append(user_input)
            print sequence
            if 'next' in T[sequence[-1]]:
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
        sauce = {
            'standalone': True,
            'sequence': sequence,
            'input_fc': input_fc,
            'output_file': output_file,
            'analysis_type': analysis_type,
            'order_by': 'Individual_ID',
        }
        # print json.dumps(sauce, indent=3, sort_keys=True)

        # Fire up Spagedi and crunch some numbers
        # spagedi = SpagediWrapper(**sauce)
        # parameters = spagedi.getParameterInfo()
        # return spagedi.execute(parameters, None)

    except Usage as e:
        print >>sys.stderr, e.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__=='__main__':
    sys.exit(main())
