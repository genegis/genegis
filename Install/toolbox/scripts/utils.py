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

def file_type(filename):
    """ Map of 'known' extensions to filetypes."""
    expected_type = None
    known_types = {
        '.csv' : 'Text',
        '.txt' : 'Text',
        '.xls' : 'Excel',
        '.xlsx': 'Excel',
    }
    ext = os.path.splitext(filename)[1].lower()
    if known_types.has_key(ext):
        expected_type = known_types[ext]
    else:
        raise UnknownType
    return expected_type 

def parse_table(input_file):
    """ Parse a text table (usually CSV) determine its type,
        and validate."""
    # TODO: handle UTF-8 encodings robustly
    header = None
    data = None
    with open(input_file, 'rb') as input_table: 
        # sample the first 4k of the file
        sample = input_table.read(4096)
        sniffer = csv.Sniffer()
    
        if not sniffer.has_header(sample):
            # require the input to have a valid header
            raise MissingCSVHeader
        else:
            dialect = sniffer.sniff(sample)
            # reset reading
            input_table.seek(0)
        
            table = csv.reader(input_table, dialect)
            # pull off the first line of the CSV
            header = table.next()
            data = []
            for row in table:
                data.append(row)
    return (header, data, dialect)

# TODO: ADD TEST CASES FOR:
#  - quoted strings inside CSV fields
#  - our various validations in validate_column_label.

def validate_table(input_file):
    (header, data, dialect) = parse_table(input_file)
    # XXX: handle TWO COLUMNS with the same name? Does ArcGIS do this automatically?
    header = [validate_column_label(column) for column in header]
    
    # set up output file name 
    temp_dir = os.path.dirname(input_file)
    temp_name = binascii.b2a_hex(os.urandom(15))
    temp_csv = os.path.join(temp_dir, temp_name)
    with open(temp_csv, 'wb') as output_file:
        writer = csv.writer(output_file, dialect=dialect)
        writer.writerow(header)
        for row in data:
            writer.writerow(row)
    return temp_csv

def validate_column_label(column):
    """
    Modify the column labels to reflect ArcGIS restrictions:
     - no spaces, replaced here with underscores.
     - no special characters: `~@#$%^&*()-+=|\,<>?/{}.!�[]:;
     - Field names need to start with a letter
     - 64 character field names
     - can't use reserved words [http://support.microsoft.com/kb/286335]

    More at: http://blogs.esri.com/esri/arcgis/2010/08/10/working-with-microsoft-excel-in-arcgis-desktop/
    """
    INVALID_CHARS = '`~@#$%^&*()-+=|\,<>?/{}.!�[]:;'

    column = column.replace(" ", "_")
    for c in INVALID_CHARS: column = column.replace(c, '')
    if not re.match('^[A-z]', column):
        column = 'genegis_' + column
    
    if len(column) > 64:
        column = column[:63]

    return column
