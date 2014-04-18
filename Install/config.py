import arcpy
import glob
import os
import ConfigParser
from collections import OrderedDict

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

def update(key, value):
    config = ConfigParser.SafeConfigParser()
    config.read(config_path)
    config.set(app_name, key, value)
    with open(config_path, 'wb') as config_file:
        config.write(config_file)        

def create(config_path):
    # initialize a basic configuration file.
    if not os.path.exists(config_path):
        if not os.path.exists(config_dir):
            os.mkdir(config_dir)
        cfg = ConfigParser.SafeConfigParser()
        cfg.add_section(app_name)
        for (var, val) in config_vars.items():
            cfg.set(app_name, var, str(val))
        with open(config_path, 'wb') as config_file:
            cfg.write(config_file)

def load(config_path, app_name):
    cfg = ConfigParser.SafeConfigParser()
    cfg.read(config_path)
    return AttrDict(cfg._sections[app_name])

app_name = 'geneGIS'
# make a configuration directory if needed
config_dir = os.path.join(os.environ['APPDATA'], app_name)
config_path = os.path.join(config_dir, "{}.cfg".format(app_name))
log_path = os.path.join(config_dir, "{}.log".format(app_name))

# clean up our temp path, if it exists
for fn in glob.glob(os.path.join(config_dir, "*.{}.tmp".format(app_name))):
    os.remove(fn)

config_vars = {
    'fc_path': None, # path to the imported feature class,
    'haplotype_path': None,
    'identification_columns': None,
    'genetic_columns': None, 
    'location_columns': None, 
    'other_columns': None, 
    'id_field': 'Individual_ID', # id field, records are unique on this identifier. 
    'srid':  4326, # the default spatial reference for data which is geographic,
                   # but otherwise unspecified. The vast majority of data 
                   # is WGS84 (SRID 4326), use it.
    'mode': 'toolbox', # default mode for tools. Expect tools to be run from a 
                      # Python toolbox, not the command-line by default.
    'log_level': 'error'
}

# initialize a basic configuration file.
if not os.path.exists(config_path):
    create(config_path)

# push out the settings into an attributed object, can pull things 
# back with 'settings.var_name'.
settings = load(config_path, app_name)

# XXX Settings in original file; reduce to core settings where possible.

selected_layer = None
selected_object = None

# these are the data types we can query.
allowed_types = ["Point", "MultiPoint"]
allowed_formats = ['FeatureClass', 'FeatureDataset']

all_layers = None

# default spatialReference id (WGS 84), updated when a layer
# is selected from the combobox.
sr = arcpy.SpatialReference(int(settings.srid))

spagedi_executable = "SPAGeDi-1.4.exe"

# map search strings to variable groups, include 'protected'
# column to explicitly define type for these columns
group_expressions = [
    #  group     regex    column type
    ('Genetic', '^sex$', 'Text'),
    ('Genetic', '^haplotype$', 'Text'),
    ('Genetic', '^dlphap$', 'Text'),
    ('Genetic', '^l_', None), 
    ('Identification', '_id$', ('Long', 'Text')),
    ('Location', '^x$', None), 
    ('Location', '^y$', None),
    ('Location', 'longitude', None),
    ('Location', 'latitude', None),
    ('Other', '^date_time$', 'Text')
]

# distance units options: CENTIMETERS | DECIMALDEGREES | DECIMETERS | FEET | INCHES | KILOMETERS | METERS | MILES | MILLIMETERS | NAUTICALMILES | POINTS | UNKNOWN | YARDS
distance_units = OrderedDict([
    # metric units first, largest to smallest
    # label            abbr  Esri name     conversion factor (to m)
    ('Kilometers',    ('km', 'kilometers', 0.001)),
    ('Meters',        ('m',  'meters', 1)),
    ('Decimeter',     ('dm', 'decimeter', 10)),
    ('Centimeters',   ('cm', 'cenimeters', 100)),
    ('Millimeters',   ('mm', 'millimeters', 1000)),
    # the crown's units
    ('Nautical miles', ('nm', 'nauticalmiles', 0.000539957)),
    ('Miles',         ('mi', 'miles', 0.000621371)),
    ('Yards',         ('yd', 'yards', 1.09361)),
    ('Feet',          ('ft', 'feet', 3.28084)),
    ('Inches',        ('in', 'inches', 39.3701))
])

primary_results = None

# hack: share state on which columns should be protected against data manipulation
# columns which have explicit data typing set
protected_columns = {}

overwrite = True
arcpy.env.overwriteOutput = True
