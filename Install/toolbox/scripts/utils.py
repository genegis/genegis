# -*- coding: utf-8 -*-
import csv
import collections
import sys
import re
import os
import binascii

def parameters_from_args(defaults_tuple=None, sys_args=None):
    """Provided a set of tuples for default values, return a list of mapped
       variables."""
    defaults = collections.OrderedDict(defaults_tuple)
    if defaults_tuple is not None:
        args = len(sys_args) - 1
        for i, key in enumerate(defaults.keys()):
            idx = i + 1
            if idx <= args:
                defaults[key] = sys_args[idx]
    return defaults

def msg(output_msg, mtype='message', exception=None):
    if mtype == 'error':
        arcpy_messages = arcpy.GetMessages()
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        if config.mode == 'script':
            if exception:
                # print the raw exception
            print exception
            # Arcpy and Python stuff, hopefully also helpful
            err_msg = "ArcPy Error: {msg_text}\nPython Error: ${tbinfo}".format(
                msg_text=arcpy_messages, tbinfo=tbinfo)
        else:
            arcpy.AddMessage(output_msg)
            if exception:
                arcpy.AddError(exception)
            arcpy.AddError(arcpy_messages)
            arcpy.AddMessage("Python Error: ${tbinfo}".format(tbinfo=tbinfo))
    elif config.mode == 'script':
        print output_msg
    else:
        if mtype == 'message':
            arcpy.AddMessage(output_msg)
        elif mtype == 'warning':
            arcpy.AddWarning(output_msg)

