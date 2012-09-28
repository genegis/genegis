selected_layer = None
selected_object = None

# these are the data types we can query.
allowed_types = ["Point", "MultiPoint"]

# id field, records are unique on this identifier.
#   FIXME: this is currently hard-coded, needs to reflect the 'ID' 
#   column chosen during the import process.
id_field = "Individual_ID"

# default spatialReference id (WGS 84).
srid = 4326
