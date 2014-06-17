#!/usr/bin/env python
"""
Standalone script to test drive SPAGeDi functionality.
"""
import os, re, sys, time, platform, glob, getopt, traceback, subprocess
from functools import wraps
from random import randint
from collections import deque
import xml.etree.cElementTree as et
from pprint import pprint as pp
from usage import Usage
from spagedi_tree import spagedi_tree, prp

class SpagediWrapper(object):

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


def spagedi_user_inputs(T, sequence):
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
                if not os.path.exists(user_input):
                    user_input = u.default

            # If we're expecting a number, check to make sure the user
            # has entered a number
            elif u.input_type == 'number':
                is_number = False
                while not is_number:
                    try:
                        temp = float(user_input)
                        is_number = True
                    except TypeError as e:
                        print "Input must be a number, try again"

            sequence.append(user_input)
        spagedi_user_inputs(T.next, sequence)

    # Prompt user to select an item from a menu
    else:
        options = sorted(T.items())
        for key, item in options:
            print key + '.', item.label
        while True:
            user_input = raw_input("Selection: ")
            if user_input in T:
                break
            print "Please select one of the options."
        sequence.append(user_input)
        if 'next' in T[sequence[-1]]:
            spagedi_user_inputs(T[sequence[-1]].next, sequence)
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
        output_file = r"C:\Users\Sparky\src\genegis\tests\data\test_spagedi_export.txt"
        testing = False
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                print __doc__
                return 0
        
        # Prompt the user: what test are we doing?
        sequence = spagedi_user_inputs(SpagediWrapper.TREE, [])
        for i, cmd in enumerate(sequence):
            if cmd == u'spagedi_file_path':
                sequence[i] = input_fc
        analysis_type = SpagediWrapper.TREE[sequence[0]].next[sequence[1]].next[sequence[2]].label

    except Usage as e:
        print >>sys.stderr, e.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == '__main__':
    sys.exit(main())
