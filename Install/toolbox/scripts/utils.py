# -*- coding: utf-8 -*-
import csv
import collections
import sys
import re
import os
import binascii
import itertools
import traceback

# enable local imports; redirect config calls to general config
import add_install_path
import config
settings = config.settings()

try:
    import arcpy

except:
    """
    The config import above thows a warning in this case,
    just swallow it here and let this script import, since most of
    these utils don't depend on arcpy.
    """
    pass

class Loci(object):
    """ A basic class to store the Loci attributes we commonly use."""
    def __init__(self, input_features):
        self.fields = self.loci_fields(input_features)
        self.count = self.loci_count()
        self.columns = self.loci_columns()
        self.names = self.loci_names()

    def loci_fields(self, input_features):
        """ Actual loci field names, e.g. L_Ev23_1."""
        # map loci fields to values
        loci = collections.OrderedDict()
        # optional: use this to also filter if the genetic columns are up to date
        genetic_columns = settings.genetic_columns.split(";")
        loci_expr = '^l_(.*)_[0-9]+'
        for field in [f.name for f in arcpy.ListFields(input_features)]:
            match = re.match(loci_expr, field, re.IGNORECASE)
            if match:
                name = match.groups()[0]
                if loci.has_key(name):
                    loci[name].append(field)
                else:
                    loci[name] = [field]
        return loci

    def defined(self):
        """ Are any loci fields defined?"""
        defined = False
        if self.column is not None:
            defined = True
        return defined

    def loci_count(self):
        """ Number of distinct loci containing fields."""
        return len(self.fields.keys())

    def loci_columns(self):
        """ All column names containing loci."""
        loci = self.fields
        return list(itertools.chain(*loci.values()))

    def loci_names(self):
        """ Loci names, e.g. Ev23."""
        loci = self.fields
        return loci.keys()

class Haplotype(object):
    """ Track our Haplotype column, and provide a few useful summarizations
        of the data contained within."""

    def __init__(self, input_features):
        self.column = self.haplotype_column(input_features)
        self.defined = self.defined()
        self.counter = self.haplotype_data(input_features)
        self.names = self.haplotype_names()
        self.indexed = self.haplotype_indexed()

    def haplotype_column(self, input_features):
        """ The column name containin the haplotype data."""
        haplo_col = None
        haplo_expr = '^haplotype|dlphap$'
        for field in [f.name for f in arcpy.ListFields(input_features)]:
            match = re.match(haplo_expr, field, re.IGNORECASE)
            if match:
                haplo_col = field
        return haplo_col

    def defined(self):
        """ Is a haplotype column defined?"""
        defined = False
        if self.column is not None:
            defined = True
        return defined

    def haplotype_data(self, input_features):
        """ Counts of each haplotype type."""
        # TODO: this currently just looks up all the data,
        # better yet we should generate a table on import and keep it updated
        # when edits are made to the input table.
        haplo_data = {}
        if self.defined:
            res = [r[0] for r in arcpy.da.SearchCursor(input_features, [self.column])]
            haplo_data = collections.Counter(filter(None, res))
        return haplo_data

    def haplotype_names(self):
        """ Distinct haplotype names found."""
        return self.counter.keys()

    def haplotype_indexed(self):
        """ A mapping of haplotype name to integers for interchange."""
        # map sorted haplotypes to integers; equivalent to Shepherd's approach
        sorted_cols = sorted(self.names)
        counter = self.counter
        counts = [counter[col] for col in sorted_cols]

        # 1: A+, 2: E1, ...
        return zip(itertools.count(1), sorted_cols, counts)

class MissingCSVHeader(Exception):
    def __init__(self, csv):
        self.csv = csv
        Exception.__init__(self, "CSV file is missing a header: {}".format(csv))

def parameters_from_args(defaults_tuple=None, sys_args=None):
    """Provided a set of tuples for default values, return a list of mapped
       variables."""
    defaults = collections.OrderedDict(defaults_tuple)
    if defaults is not None:
        args = len(sys_args) - 1
        for i, key in enumerate(defaults.keys()):
            idx = i + 1
            if idx <= args:
                defaults[key] = sys_args[idx]
            else:
                msg("Missing argument {}, using default `{}`".format(
                        key, defaults[key]))
    return defaults

def msg(output_msg, mtype='message', exception=None):
    if mtype == 'error':
        arcpy_messages = arcpy.GetMessages()
        try:
            tb = sys.exc_info()[2]
            tbinfo = traceback.format_tb(tb)[0]
        except:
            tbinfo = "No traceback reported."

        if settings.mode == 'script':
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
    elif settings.mode == 'script':
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
        '.asc' : 'Text',
        '.tab' : 'Text',
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
    dialect = None
    try:
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
                # for reading, rely on dialect parsing to correctly dermine
                # the input file's traits (e.g. proper quoting).
                table = csv.reader(input_table, dialect=dialect)

                # pull off the first line of the CSV
                header = table.next()
                data = []
                for row in table:
                    data.append(row)
    except Exception as e:
        raise e
    return (header, data, dialect)

# TODO: ADD TEST CASES FOR:
#  - quoted strings inside CSV fields
#  - our various validations in validate_column_label.

def validate_table(input_file):
    (header, data, dialect) = parse_table(input_file)

    # Handle multiple columns with the same name
    validated_header = []
    # Generate a list of columns which have duplicate names.
    duplicate_cols = set([i for i in header if header.count(i) > 1])
    duplicate_positions = collections.Counter(duplicate_cols)
    for col in header:
        label = validate_column_label(col)
        # handle the duplicate columns, labeling each item uniquely
        if col in duplicate_cols:
            # get current dupe position
            label = label + "_" + str(duplicate_positions[col])
            duplicate_positions[col] += 1
        validated_header.append(label)

    # set up output file name
    temp_dir = os.path.dirname(input_file)
    (label, ext) = os.path.splitext(os.path.basename(input_file))

    # generate a random name, but include the original file suffix for Arc
    temp_name = binascii.b2a_hex(os.urandom(15))
    tmp_fn = "".join([temp_name, ext])
    temp_csv = os.path.join(temp_dir, tmp_fn)

    with open(temp_csv, 'wb') as output_file:
        writer = csv.writer(output_file, dialect=dialect, quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(validated_header)
        for row in data:
            writer.writerow(row)
    return temp_csv

def validated_table_results(input_file):
    validated_table = validate_table(input_file)
    table_parts = parse_table(validated_table)
    # delete the temporary table generated; only want the components in this case.
    os.unlink(validated_table)
    return table_parts

def validate_column_label(column):
    """
    Modify the column labels to reflect ArcGIS restrictions:
     - no spaces, replaced here with underscores.
     - no special characters: `~@#$%^&*()-+=|\,<>?/{}.!’[]:;
     - Field names need to start with a letter
     - 64 character field names
     - can't use reserved words [http://support.microsoft.com/kb/286335]

    Alternatively, can use ValidateFieldName for a similar effect,
    without the same fine-grained control:
      http://resources.arcgis.com/en/help/main/10.1/index.html#//018v00000060000000
    """
    INVALID_CHARS = '`~@#$%^&*()+=|\,<>?/{}.!’[]:;'

    # replace a few common characters with underscores
    column = column.replace(" ", "_").replace("-", "_")
    for c in INVALID_CHARS: column = column.replace(c, '')
    # if the column starts with non-text, prefix the string with 'genegis'
    if not re.match('^[A-z]', column):
        column = 'genegis_' + column

    # 'Field names are limited to 64 characters for both file and
    # personal geodatabases.'
    if len(column) > 64:
        column = column[:63]

    return column

def protect_columns(input_table_name=None, protected_columns={}):
    """
    Force data typing on columns using schema.ini to store the necessary
    configuration. This prevents ArcGIS from trying to auto-detect the
    data type, which doesn't work for some of our input data, such as
    haplotypes, which it wants to treat as coordinate values.
    """

    # input table directory
    input_dir = os.path.dirname(input_table_name)

    # just the table name
    table_name = os.path.basename(input_table_name)

    # open the relevant schema.ini file
    schema_path = os.path.join(input_dir, 'schema.ini')

    # If it exists already, we want append. Don't use binary mode, let
    # Python auto-conver the newlines.
    if os.path.exists(schema_path):
        mode = 'a+'
    else:
        mode = 'w+'
    with open(schema_path, mode) as schema_file:
        header = "[{table_name}]\n".format(table_name=table_name)
        schema_file.write(header)
        if protected_columns:
            for (value, res_dict) in protected_columns.items():
                (idx, data_type) = res_dict
                col_label = "Col{idx}={value} {data_type}\n".format(
                    idx=idx, value=value, data_type=data_type)
                schema_file.write(col_label)

    return schema_path

def set_file_extension(param, ext):
    # make sure the output file name has the correct extension.
    param_input = param.valueAsText
    if param_input is not None:
        param_output = add_file_extension(param_input, ext)
    else:
        param_output = param_input
    return param_output

def add_file_extension(input_name, expected_ext):
    name_with_ext = input_name
    ext = expected_ext.lower()
    (label, input_ext) = os.path.splitext(os.path.basename(input_name))
    if input_ext.lower() != ext:
        name_with_ext = "{label}.{ext}".format(label = label, ext=ext)
    return os.path.join(os.path.dirname(input_name), name_with_ext)

def xstr(s):
    """ Replace None values with empty strings."""
    if s is None:
        return ''
    return str(s)

def zstr(s):
    """ Replace None values with zeros."""
    if s is None:
        return '0'
    return str(s)

# FIXME: duplicated from Install\utils.py
def currentLayers():
    # find layers in current map document
    layers = []
    # inspect the layer list, find the first point layer
    mxd = arcpy.mapping.MapDocument("current")
    # get a list of all layers, store it
    config.all_layers = arcpy.mapping.ListLayers(mxd)

    # iterate over our layers, find those which are candidates for analysis
    if config.all_layers is not None:
        for layer in config.all_layers:
            try:
                # FIXME: check performance on this. if expensive, do something cheaper
                desc = arcpy.Describe(layer)
                if desc.datasetType in config.allowed_formats and \
                    desc.shapeType in config.allowed_types:
                    layers.append(layer)
            except:
                # silently skip layers which don't support describe (e.g. AGOL).
                continue
    return layers
