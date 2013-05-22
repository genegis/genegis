import arcpy
import os
import ConfigParser

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
        for var in config_vars:
            cfg.set(app_name, var, 'None')
        with open(config_path, 'wb') as config_file:
            cfg.write(config_file)
    
# make a configuration directory if needed
config_dir = os.path.join(os.environ['APPDATA'], app_name)
config_path = os.path.join(config_dir, "%s.cfg" % app_name)

config_vars = {
    'app_name': 'geneGIS',
    'fc_path': None, # path to the imported feature class
    'identification_columns': None,
    'genetic_columns': None, 
    'location_columns': None, 
    'other_columns': None, 
    'id_field': 'Individual_ID', # id field, records are unique on this identifier. 
    'mode': 'toolbox', # default mode for tools. Expect tools to be run from a 
                      # Python toolbox, not the command-line by default.
    'srid':  4326 # the default spatial reference for data which is geographic,
                   # but otherwise unspecified. The vast majority of data 
                   # is WGS84 (SRID 4326), use it.
}

# initialize a basic configuration file.
if not os.path.exists(config_path):
    create(config_path)

cfg = ConfigParser.SafeConfigParser()
cfg.read(config_path)
# push out the settings into an attributed object, can pull things 
# back with 'settings.var_name'.
settings = AttrDict(cfg._sections[app_name])

# XXX Settings in original file; reduce to core settings where possible.

selected_layer = None
selected_object = None

# these are the data types we can query.
allowed_types = ["Point", "MultiPoint"]
allowed_formats = ['FeatureClass', 'FeatureDataset']

all_layers = None

# default spatialReference id (WGS 84), updated when a layer
# is selected from the combobox.
sr = arcpy.SpatialReference(settings.srid)

# map search strings to variable groups, include 'protected'
# column to explicitly define type for these columns
group_expressions = [
    #  group     regex    column type
    ('Genetic', '^sex$', 'Text'),
    ('Genetic', '^haplotype$', 'Text'),
    ('Genetic', '^dlphap$', 'Text'),
    ('Genetic', '^l_', None), 
    ('Identification', '_id$', 'Text'),
    ('Location', '^x$', None), 
    ('Location', '^y$', None),
    ('Location', 'longitude', None),
    ('Location', 'latitude', None),
    ('Other', '^date_time$', 'Text')
]

# XXX Settings below imported from toolbox/scripts/config.py

# same thing, as string; used by geoprocessing tools.
DEFAULT_SR = sr.exportToString()

primary_results = None

# hack: share state on which columns should be protected against data manipulation
# columns which have explicit data typing set
protected_columns = {}

overwrite = True
arcpy.env.overwriteOutput = True
