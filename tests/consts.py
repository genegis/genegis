
import os

local_path = os.path.dirname(__file__)
data_path = os.path.join(local_path, 'data')

# testing-specific datasets.
test_csv_doc = os.path.join(data_path, 'SRGD_example.csv')
test_csv_with_comment_field = os.path.join(data_path, 'SRGD_with_comment_field.csv')
test_csv_full = os.path.join(data_path, 'SRGD_export_demodna.csv.gz')

# A File Geodatabasee with an imported SRGD file and test raster.
test_fgdb = os.path.join(data_path, 'test.gdb')
test_fgdb_fc = os.path.join(test_fgdb, 'SRGD_export_demodna_Spatial')
test_fgdb_raster = os.path.join(test_fgdb, 'etopo1_downsampled_clipped')

# our default set of columns.
genetic_columns = "Sex;Haplotype;L_GATA417_1;L_GATA417_2;L_Ev37_1" + \
        ";L_Ev37_2;L_Ev96_1;L_Ev96_2;L_rw4_10_1;L_rw4_10_2"
id_columns = "Sample_ID;Individual_ID"
loc_columns = "Longitude;Latitude"
other_columns = "Region"
protected_columns = {}

# location of the python toolbox.
pyt_file = os.path.abspath(
                os.path.join(local_path, '..', 'Install', 'toolbox', 'genegis.pyt'))
