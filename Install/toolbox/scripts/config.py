import os
import arcpy

app_name = 'geneGIS'

# make a configuration directory
config_dir = os.path.join(os.environ['APPDATA'], app_name)
if not os.path.exists(config_dir):
    os.mkdir(config_dir)

fc_path_file = os.path.join(config_dir, 'feature-class.txt')

# default mode for tools. Expect tools to be run from a Python toolbox,
# not the command line by default.
mode = 'toolbox'

overwrite = True
arcpy.env.overwriteOutput = True
# the default spatial reference for data which is geographic, but otherwise
# unspecified. The vast majority of data is WGS84 (SRID 4326), use it.
DEFAULT_SR = ("GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',"
            "SPHEROID['WGS_1984',6378137.0,298.257223563]],"
            "PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400"
            "-400 1000000000;-100000 10000;-100000 "
            "10000;8.98315284119521E-09;0.001;0.001;IsHighPrecision")
