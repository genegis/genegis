import os
import sys
import unittest

import arcpy
import zipfile
from geographiclib.geodesic import Geodesic

from tempdir import TempDir

import consts
import utils

# import our local directory so we can use the internal modules
import_paths = ['../Install/toolbox', '../Install']
utils.addLocalPaths(import_paths)

from scripts import ClassifiedImport, DistanceMatrix, ShortestDistancePaths

# A GDB for our test results
d = TempDir()
output_dir = d.name
output_gdb = 'test_genegis'
gdb_path = os.path.join(output_dir, "%s.gdb" % output_gdb)

class TestExampleDataExists(unittest.TestCase):

    def testCsvExampleExists(self):
        self.assertTrue(os.path.exists(consts.test_csv_doc))

    def testCsvDocumentExists(self):
        self.assertTrue(os.path.exists(consts.test_csv_with_comment_field))

class TestClassifiedImport(unittest.TestCase):

    """
    ClassifiedImport.main(input_table=None, sr=None, output_loc=None,
    output_gdb=None, output_fc=None, genetic=None,
    identification=None, location=None, other=None,
    mode=consts.settings.mode, protected_map=consts.protected_columns)
    """
    def setUp(self):
        self.output_fc = os.path.join(gdb_path, "test_csv_spatial")

    def testClassifiedImportAvailable(self, method=ClassifiedImport):
        self.assertTrue('main' in vars(method))

    def testClassifiedImportRun(self, method=ClassifiedImport):
        # clean up from any past runs
        arcpy.Delete_management(gdb_path)

        method.main(input_table=consts.test_csv_doc, 
                sr=None, output_loc=output_dir, 
                output_gdb=output_gdb, output_fc=self.output_fc,
                genetic=consts.genetic_columns, 
                identification=consts.id_columns, location=consts.loc_columns, 
                other=consts.other_columns, mode='script')
        self.assertTrue(os.path.exists(gdb_path))

        # test that the input columns exist. Note that in the general case,
        # these column names may be remapped, but here we're using presets
        # which already conform to the naming requirements.
        input_columns = ";".join([consts.genetic_columns, consts.id_columns, \
                consts.loc_columns, consts.other_columns]).split(";")
        output_columns = [f.name for f in arcpy.ListFields(self.output_fc)]
        for column in input_columns:
            self.assertTrue(column in output_columns)

    def testToolboxImport(self):
        self.toolbox = arcpy.ImportToolbox(consts.pyt_file)
        self.assertTrue('ClassifiedImport' in vars(self.toolbox))

    def testCleanup(self):
        # clean up
        arcpy.Delete_management(gdb_path)
        self.assertFalse(os.path.exists(gdb_path))


class TestDistanceMatrix(unittest.TestCase):

    def setUp(self):
        self.input_fc = "in_memory/temp"
        scriptloc = os.path.dirname(os.path.realpath(__file__))
        self.output = os.path.join(scriptloc, 'data', 'Test_DistanceMatrix')

        # Use the SRGD_example_Spatial layer from genegis.mxd for testing
        mxdpath = os.path.abspath(
            os.path.join(scriptloc, os.path.pardir, 
                         'Install', 'toolbox', 'genegis.mxd')
        )
        mxd = arcpy.mapping.MapDocument(mxdpath)
        for lyr in arcpy.mapping.ListLayers(mxd):
            if lyr.name == 'SRGD_example_Spatial':
                arcpy.CopyFeatures_management(lyr, self.input_fc)
                break

    def testDistanceMatrixAvailable(self, method=DistanceMatrix):
        self.assertTrue('main' in vars(method))

    def testDistanceMatrixRun(self, method=DistanceMatrix):
        # clean up from any past runs
        arcpy.Delete_management(self.output)

        parameters = {
            'input_fc': self.input_fc,
            'dist_unit': 'Kilometers',
            'matrix_type': 'Square',
            'output_matrix': self.output,
        }
        method.main(mode='script', **parameters)

        # Calculate a "reference" distance matrix using geographiclib.
        # This will be used to check the output of DistanceMatrix.py.
        input_fc_mem = 'in_memory/input_fc'
        arcpy.CopyFeatures_management(self.input_fc, input_fc_mem)
        WGS84 = arcpy.SpatialReference('WGS 1984')
        cursor = arcpy.da.SearchCursor(input_fc_mem, ['OID@', 'SHAPE@XY'],
                                       spatial_reference=WGS84)
        points = {}
        for row in cursor:
            points[row[0]] = (row[1][0], row[1][1])
        ref_dist = {}
        for from_fid, from_point in points.items():
            ref_dist[from_fid] = {}
            for to_fid, to_point in points.items():
                if from_fid == to_fid:
                    ref_dist[from_fid][to_fid] = 0
                else:
                    ref_dist[from_fid][to_fid] = Geodesic.WGS84.Inverse(
                        from_point[1], from_point[0], to_point[1], to_point[0]
                    )['s12'] / 1000.0

        # Sanity checks for the distance matrix:
        # 1. It must exist
        # 2. The first row must contain point indices 1, 2, 3, ...
        # 3. The first entry in each row should contain its point index
        # 4. The diagonal entries should all be 0
        # 5. All entries should be positive
        # 6. There should be the same number of rows and columns
        # 7. The distances should be the same as reported by geographiclib
        # 8. The matrix must be symmetric (distances a->b & b->a must be equal)
        #
        # Sanity check 1
        self.assertTrue(arcpy.Exists(self.output))
        with open(self.output, 'rU') as outfile:
            for i, line in enumerate(outfile):
                row = line.strip().split(',')
                # Sanity check 2
                if i == 0:
                    self.assertListEqual(map(int, row[1:]), range(1, len(row)))
                else:
                    row = map(float, row)
                    # Sanity check 3
                    self.assertEqual(i, row[0])
                    # Sanity check 4
                    self.assertEqual(0, row[i])
                    # Sanity check 5
                    self.assertTrue(all([j >= 0 for j in row]))
                    # Sanity check 7
                    # (distances rounded to the nearest 0.001 km)
                    for j, dist in enumerate(row[1:]):
                        rounded_ref_dist = round(ref_dist[int(row[0])][j+1], 3)
                        self.assertEqual(round(dist, 3), rounded_ref_dist)
            # Sanity check 6
            self.assertEqual(i+1, len(row))
            # Sanity check 8
            # (using reference matrix, which we already verified is the same
            # as the matrix calculated by DistanceMatrix.py, in check 7)
            ref_matrix = [dist.values() for row, dist in ref_dist.items()]
            ref_matrix_transpose = map(list, zip(*ref_matrix))
            self.assertEqual(ref_matrix, ref_matrix_transpose)

    def testToolboxImport(self):
        self.toolbox = arcpy.ImportToolbox(consts.pyt_file)
        self.assertTrue('DistanceMatrix' in vars(self.toolbox))

    def testCleanup(self):
        # clean up
        arcpy.Delete_management(self.output)


class TestShortestDistancePaths(unittest.TestCase):

    def setUp(self):
        self.input_fc = "in_memory/temp"
        scriptloc = os.path.dirname(os.path.realpath(__file__))
        self.output_fc = os.path.join(scriptloc, 'data', 'Test_ShortestDistancePaths')

        # Use the SRGD_example_Spatial layer from genegis.mxd for testing
        mxdpath = os.path.abspath(
            os.path.join(scriptloc, os.path.pardir, 
                         'Install', 'toolbox', 'genegis.mxd')
        )
        mxd = arcpy.mapping.MapDocument(mxdpath)
        for lyr in arcpy.mapping.ListLayers(mxd):
            if lyr.name == 'SRGD_example_Spatial':
                arcpy.CopyFeatures_management(lyr, self.input_fc)
                break

    def testShortestDistancePathsAvailable(self, method=ShortestDistancePaths):
        self.assertTrue('main' in vars(method))

    def testShortestDistancePathsRun(self, method=ShortestDistancePaths):
        # clean up from any past runs
        arcpy.Delete_management(self.output_fc)

        parameters = {
            'input_fc': self.input_fc,
            'output_fc': self.output_fc,
        }
        method.main(mode='script', **parameters)
        arcpy.DeleteFeatures_management(self.input_fc)

        output_file_extensions = ('.cpg', '.dbf', '.prj', '.sbn',
                                  '.sbx', '.shp', '.shp.xml', '.shx')
        for ext in output_file_extensions:
            output_file = self.output_fc + ext
            self.assertTrue(arcpy.Exists(output_file))

    def testToolboxImport(self):
        self.toolbox = arcpy.ImportToolbox(consts.pyt_file)
        self.assertTrue('ShortestDistancePaths' in vars(self.toolbox))

    def testCleanup(self):
        arcpy.Delete_management(self.output_fc)


class TestQuotedMultilineInput(unittest.TestCase):
    
    def setUp(self):
        self.output_fc = os.path.join(gdb_path, "test_multiline_spatial")

    def testClassifiedImportRun(self, method=ClassifiedImport):
        # include comment field in 'other' fields.
        other_columns = "Region;Comment"

        # clean up from any past runs
        arcpy.Delete_management(gdb_path)

        method.main(input_table=consts.test_csv_with_comment_field, 
                sr=None, output_loc=output_dir, 
                output_gdb=output_gdb, output_fc=self.output_fc,
                genetic=consts.genetic_columns, identification=consts.id_columns, 
                location=consts.loc_columns, other=consts.other_columns, mode='script')
        self.assertTrue(os.path.exists(gdb_path))

        # test our comment field is set
        self.assertTrue("Comment" in [f.name for f in arcpy.ListFields(self.output_fc)])
        res = [r[0] for r in arcpy.da.SearchCursor(self.output_fc, ['Comment'])]

        expected_value = 'This is a test comment field, which contains, among ' + \
                'other things, "quoted statements", which are useful for testing ' + \
                'the CSV parser.\n Now, a new line.'
        self.assertTrue(res[0] == expected_value) 
        
    def testCleanup(self):
        # clean up
        arcpy.Delete_management(gdb_path)
        self.assertFalse(os.path.exists(gdb_path))


# this test should be run after a fresh run of makeaddin to rebuild the .esriaddin file.
class TestAddin(unittest.TestCase):
    def setUp(self):
        self.addin_path = os.path.abspath(os.path.join('..', 'genegis.esriaddin'))
        self.addin_zip = zipfile.ZipFile(self.addin_path, 'r')

    def testToolboxIsPresent(self):
        toolbox_path = 'Install/toolbox/genegis.pyt' 
        self.assertTrue(toolbox_path in self.addin_zip.namelist())

if __name__  == '__main__':
    unittest.main()
