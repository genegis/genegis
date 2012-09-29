import arcpy

selected_layer = None
selected_object = None

# these are the data types we can query.
allowed_types = ["Point", "MultiPoint"]
allowed_formats = ['FeatureClass', 'FeatureDataset']


# id field, records are unique on this identifier.
#   FIXME: this is currently hard-coded, needs to reflect the 'ID' 
#   column chosen during the import process.
id_field = "Individual_ID"

# default spatialReference id (WGS 84), updated when a layer
# is selected from the combobox.
srid = 4326
sr = arcpy.SpatialReference(srid)

primary_results = None
