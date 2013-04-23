import arcpy
import os

selected_layer = None
selected_object = None

# these are the data types we can query.
allowed_types = ["Point", "MultiPoint"]
allowed_formats = ['FeatureClass', 'FeatureDataset']

all_layers = None

# id field, records are unique on this identifier.
#   FIXME: this is currently hard-coded, needs to reflect the 'ID' 
#   column chosen during the import process.
id_field = "Individual_ID"

# default spatialReference id (WGS 84), updated when a layer
# is selected from the combobox.
srid = 4326
sr = arcpy.SpatialReference(srid)

primary_results = None

# hack: share state on which columns should be protected against data manipulation
# columns which have explicit data typing set
protected_columns = {}
app_name = 'geneGIS'

# make a configuration directory if needed
config_dir = os.path.join(os.environ['APPDATA'], app_name)
if not os.path.exists(config_dir):
    os.mkdir(config_dir)
fc_path_file = os.path.join(config_dir, 'feature-class.txt')
