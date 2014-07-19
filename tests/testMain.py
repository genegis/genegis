import os
import sys
import unittest

import arcpy
import csv
import datetime
import gzip
import hashlib
import zipfile
from collections import Counter
from geographiclib.geodesic import Geodesic

import consts
import utils

# import our local directory so we can use the internal modules
import_paths = ['../Install/toolbox', '../Install', '../Install/toolbox/lib']
utils.addLocalPaths(import_paths)

from tempdir import TempDir
from scripts import ClassifiedImport, DistanceMatrix, ShortestDistancePaths, \
        ExtractRasterValuesToPoints, ExportToGenAlEx, ExportToSRGD, ExportToAIS, \
        ExportToGenepop, IndividualPaths, utils as script_utils

# A GDB for our test results
class CoreFGDB(object):
    """ Create a FGDB and a test table inside for reuse in the tests."""

    def __init__(self):
        self.d = TempDir()
        self.dir_path = self.d.name
        self.name = 'test_genegis'
        self.path = os.path.join(self.dir_path, "%s.gdb" % self.name)
        self.input_fc = os.path.join(self.path, "test_spatial")
        self.input_fc_mem = 'in_memory/test_spatial'

        # populate the feature with valid data
        self.create_feature()
        self.feature_to_mem()

    def create_feature(self):
        # create a spatial table to use for testing.
        ClassifiedImport.main(input_table=consts.test_csv_doc,
                sr=None, output_loc=self.dir_path,
                output_gdb=self.name, output_fc=self.input_fc,
                genetic=consts.genetic_columns,
                identification=consts.id_columns, location=consts.loc_columns,
                other=consts.other_columns, mode='script')
        return

    def feature_to_mem(self):
        arcpy.CopyFeatures_management(self.input_fc, self.input_fc_mem)

fgdb = CoreFGDB()

# data-oriented tests
#
class TestExampleData(unittest.TestCase):
    """ Ensure we can find our expected test datasets."""

    # input SRGD files
    def testCsvExampleExists(self):
        self.assertTrue(os.path.exists(consts.test_csv_doc))

    def testCsvDocumentExists(self):
        self.assertTrue(os.path.exists(consts.test_csv_with_comment_field))

    def testCsvFullExists(self):
        self.assertTrue(os.path.exists(consts.test_csv_full))

        # test that the file is the same data we expect.
        sha1 = hashlib.sha1()
        with open(consts.test_csv_full, 'rb') as f:
            sha1.update(f.read())
        self.assertTrue(sha1.hexdigest() == \
                'a6637c760df88efa1f8013d4c91f37ae6f5e183d')

    # test our existing FGDB source
    def testFgdbExists(self):
        self.assertTrue(arcpy.Exists(consts.test_fgdb))

        desc = arcpy.Describe(consts.test_fgdb)
        self.assertEqual(desc.dataType, 'Workspace')
        self.assertEqual(desc.release, '3,0,0')
        self.assertEqual(desc.workspaceFactoryProgId, \
                u'esriDataSourcesGDB.FileGDBWorkspaceFactory.1')

    def testFgdbFc(self):
        fields = ['OBJECTID', 'Shape', 'Sample_ID', 'Individual_ID', 'Latitude',
                'Longitude', 'Date_Time', 'Region', 'Sex', 'Haplotype', 'L_Ev1_1',
                'L_Ev1_2', 'L_Ev104_1', 'L_Ev104_2', 'L_Ev14_1', 'L_Ev14_2',
                'L_Ev21_1', 'L_Ev21_2', 'L_Ev37_1', 'L_Ev37_2', 'L_Ev94_1',
                'L_Ev94_2', 'L_Ev96_1', 'L_Ev96_2', 'L_GATA28_1', 'L_GATA28_2',
                'L_GATA417_1', 'L_GATA417_2', 'L_GT211_1', 'L_GT211_2', 'L_GT23_1',
                'L_GT23_2', 'L_GT575_1', 'L_GT575_2', 'L_rw4_10_1', 'L_rw4_10_2',
                'L_rw48_1', 'L_rw48_2', 'Occurrence_ID', 'Date_formatted']
        self.assertTrue(arcpy.Exists(consts.test_fgdb_fc))

        desc = arcpy.Describe(consts.test_fgdb_fc)
        self.assertEqual(desc.dataType, 'FeatureClass')
        self.assertEqual(desc.shapeType, 'Point')

        fc_fields = [f.name for f in desc.fields]
        for field in fields:
            self.assertTrue(field in fc_fields)

    def testFgdbRaster(self):
        self.assertTrue(arcpy.Exists(consts.test_fgdb_raster))

        desc = arcpy.Describe(consts.test_fgdb_raster)
        self.assertEqual(desc.dataType, 'RasterDataset')
        self.assertEqual(desc.format, 'FGDBR')
        self.assertEqual(desc.pixelType, 'S16') # 16-bit integer values
        self.assertEqual(desc.width, 431)
        self.assertEqual(desc.height, 415)
        # test for an expected mean value
        ar = arcpy.GetRasterProperties_management(consts.test_fgdb_raster, 'MEAN')
        mean_value = float(ar.getOutput(0))
        self.assertAlmostEqual(mean_value, -1582.89427780728)

class TestQuotedMultilineInput(unittest.TestCase):
    """ Test validation for complicated input SRGD files."""
    def setUp(self):
        self.output_fc = os.path.join(fgdb.path, "test_multiline_spatial")

    def testClassifiedImportRun(self, method=ClassifiedImport):
        # include comment field in 'other' fields.
        other_columns = "Region;Comment"

        method.main(input_table=consts.test_csv_with_comment_field,
                sr=None, output_loc=fgdb.dir_path,
                output_gdb=fgdb.name, output_fc=self.output_fc,
                genetic=consts.genetic_columns, identification=consts.id_columns,
                location=consts.loc_columns, other=consts.other_columns, mode='script')
        self.assertTrue(os.path.exists(fgdb.path))

        # test our comment field is set
        self.assertTrue("Comment" in [f.name for f in arcpy.ListFields(self.output_fc)])
        res = [r[0] for r in arcpy.da.SearchCursor(self.output_fc, ['Comment'])]

        expected_value = 'This is a test comment field, which contains, among ' + \
                'other things, "quoted statements", which are useful for testing ' + \
                'the CSV parser.\n Now, a new line.'
        self.assertTrue(res[0] == expected_value)

    def tearDown(self):
        # clean up
        arcpy.Delete_management(self.output_fc)

# class tests
class TestLoci(unittest.TestCase):

    def setUp(self):
        self.input_features = consts.test_fgdb_fc
        self.loci_names = ['Ev1', 'Ev104', 'Ev14', 'Ev21', 'Ev37', 'Ev94', 'Ev96',
                'GATA28', 'GATA417', 'GT211', 'GT23', 'GT575', 'rw4_10', 'rw48']
        self.loci_columns = ['L_Ev1_1', 'L_Ev1_2', 'L_Ev104_1', 'L_Ev104_2', 'L_Ev14_1',
                'L_Ev14_2', 'L_Ev21_1', 'L_Ev21_2', 'L_Ev37_1', 'L_Ev37_2', 'L_Ev94_1',
                'L_Ev94_2', 'L_Ev96_1', 'L_Ev96_2', 'L_GATA28_1', 'L_GATA28_2',
                'L_GATA417_1', 'L_GATA417_2', 'L_GT211_1', 'L_GT211_2',
                'L_GT23_1', 'L_GT23_2', 'L_GT575_1', 'L_GT575_2', 'L_rw4_10_1',
                'L_rw4_10_2', 'L_rw48_1', 'L_rw48_2']

    def testClassExists(self):
        self.assertTrue('Loci' in dir(script_utils))

    def testLociClass(self):
        loci = script_utils.Loci(self.input_features)

        self.assertTrue(loci.defined)
        self.assertEqual(loci.names, self.loci_names)
        self.assertEqual(loci.count, 14)
        self.assertEqual(loci.columns, self.loci_columns)

class TestHaplotype(unittest.TestCase):

    def setUp(self):
        self.input_features = consts.test_fgdb_fc
        self.haplotype_names = ['F1', 'F2', 'F3', 'F4', 'F6', 'F8', 'E10', 'E13',
                'A-', 'A3', 'E5', 'E4', 'E7', 'E6', 'E1', 'A+', 'E3']
        self.counts = Counter({'F2': 57, 'E1': 34, 'E4': 12, 'A+': 9, 'F3': 8, 'E13': 7,
                'F1': 6, 'A3': 5, 'E6': 4, 'F6': 3, 'E10': 3, 'A-': 3, 'E5': 3, 'E7': 2,
                'E3': 2, 'F4': 1, 'F8': 1})

    def testClassExists(self):
        self.assertTrue('Haplotype' in dir(script_utils))

    def testLociClass(self):
        haplotype = script_utils.Haplotype(self.input_features)

        self.assertTrue(haplotype.defined)
        self.assertEqual(haplotype.column, 'Haplotype')
        self.assertEqual(haplotype.names, self.haplotype_names)
        self.assertEqual(haplotype.counter, self.counts)

# import tests
#

class TestClassifiedImport(unittest.TestCase):
    """ Test importing a sample SRGD file to a geodatabase."""

    def setUp(self):
        self.output_fc = os.path.join(fgdb.path, "test_classified_import_spatial")

    def testClassifiedImportAvailable(self, method=ClassifiedImport):
        self.assertTrue('main' in vars(method))

    def testClassifiedImportRun(self, method=ClassifiedImport):
        # clean up from any past runs
        arcpy.Delete_management(fgdb.path)

        method.main(input_table=consts.test_csv_doc,
                sr=None, output_loc=fgdb.dir_path,
                output_gdb=fgdb.name, output_fc=self.output_fc,
                genetic=consts.genetic_columns,
                identification=consts.id_columns, location=consts.loc_columns,
                other=consts.other_columns, mode='script')
        self.assertTrue(os.path.exists(fgdb.path))

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

    def tearDown(self):
        # clean up
        arcpy.Delete_management(fgdb.path)
        self.assertFalse(os.path.exists(fgdb.path))

class TestClassifiedImportFullDataset(unittest.TestCase):
    """ Test importing a full sample dataset to a geodatabase."""

    def setUp(self):
        self.output_fc = os.path.join(fgdb.path, "test_full_import_spatial")
        self.temp_srgd = os.path.join(fgdb.dir_path, "SRGD_export.csv")

    def testClassifiedImportAvailable(self, method=ClassifiedImport):
        self.assertTrue('main' in vars(method))

    def testClassifiedImportRun(self, method=ClassifiedImport):
        # write out a temporary uncompressed version
        with gzip.open(consts.test_csv_full, 'rb') as f:
            with open(self.temp_srgd, 'wb') as w:
                w.write(f.read())

        method.main(input_table=self.temp_srgd,
                sr=None, output_loc=fgdb.dir_path,
                output_gdb=fgdb.name, output_fc=self.output_fc,
                genetic=consts.genetic_columns,
                identification=consts.id_columns, location=consts.loc_columns,
                other=consts.other_columns, mode='script')
        self.assertTrue(os.path.exists(fgdb.path))

        # test that the input columns exist. Note that in the general case,
        # these column names may be remapped, but here we're using presets
        # which already conform to the naming requirements.
        input_columns = ";".join([consts.genetic_columns, consts.id_columns, \
                consts.loc_columns, consts.other_columns]).split(";")
        output_columns = [f.name for f in arcpy.ListFields(self.output_fc)]

        for column in input_columns:
            self.assertTrue(column in output_columns)

        fields = ("OID@", "Sample_ID", "Occurrence_ID", 'L_Ev1_1')
        where = '"Sample_ID" = 564'
        with arcpy.da.SearchCursor(self.output_fc, fields, where) as cursor:
            (oid, sample_id, occurence_id, hap_ev1) = cursor.next()

            self.assertEqual(occurence_id, 'CRC:Fri Jan 23 00:00:00 EST 2004:DT1:1')
            self.assertEqual(oid, 1316)
            self.assertEqual(hap_ev1, 123)

    def testToolboxImport(self):
        self.toolbox = arcpy.ImportToolbox(consts.pyt_file)
        self.assertTrue('ClassifiedImport' in vars(self.toolbox))

    def tearDown(self):
        # clean up
        arcpy.Delete_management(self.temp_srgd)
        self.assertFalse(os.path.exists(self.temp_srgd))

# geographic analysis tools
#

class TestDistanceMatrix(unittest.TestCase):
    """ Test the distance matrix on our small sample data."""

    def setUp(self):
        self.input_fc = fgdb.input_fc_mem
        self.output_dists = os.path.join(consts.data_path, 'Test_DistanceMatrix')

    def geographiclibDistances(self, input_fc):
        # Calculate a "reference" distance matrix using geographiclib.
        # This will be used to check the output of DistanceMatrix.py.
        WGS84 = arcpy.SpatialReference('WGS 1984')
        cursor = arcpy.da.SearchCursor(input_fc, ['OID@', 'SHAPE@XY'],
                                       spatial_reference=WGS84)
        points = {}
        for row in cursor:
            points[row[0]] = (row[1][0], row[1][1])
        ref_dists = {}
        for from_fid, from_point in points.items():
            ref_dists[from_fid] = {}
            for to_fid, to_point in points.items():
                if from_fid == to_fid:
                    ref_dists[from_fid][to_fid] = 0
                else:
                    dist = Geodesic.WGS84.Inverse(
                        from_point[1], from_point[0], to_point[1], to_point[0]
                    )['s12'] / 1000.0
                    ref_dists[from_fid][to_fid] = dist
        return ref_dists

    def compareDistances(self, ref_dists, output_dists, is_spagedi=False):
        """
        Sanity checks for the distance matrix:
         1. It must exist
         2. The first row must contain point indices 1, 2, 3, ...
         3. The first entry in each row should contain its point index
         4. The diagonal entries should all be 0
         5. All entries should be positive
         6. There should be the same number of rows and columns
         7. The distances should be the same as reported by geographiclib
         8. The matrix must be symmetric (distances a->b & b->a must be equal)
        """

        if is_spagedi:
            sep = '\t'
        else:
            sep = ','

        # Sanity check 1
        self.assertTrue(arcpy.Exists(output_dists))
        with open(output_dists, 'rU') as outfile:
            for i, line in enumerate(outfile):
                # SPAGeDi, end of the file
                if line == 'END\n':
                    continue
                row = line.strip().split(sep)
                # Sanity check 2
                if i == 0:
                    if not is_spagedi:
                        self.assertListEqual(map(int, row[1:]), range(1, len(row)))
                else:
                    try:
                        row = map(float, row)
                    except ValueError:
                        # something's gone wrong, show the erroneous row
                        self.assertFalse(row)
                    # Sanity check 3
                    self.assertEqual(i, row[0])
                    # Sanity check 4
                    self.assertEqual(0, row[i])
                    # Sanity check 5
                    self.assertTrue(all([j >= 0 for j in row]))
                    # Sanity check 7
                    # (distances rounded to the nearest 0.001 km)
                    for j, dist in enumerate(row[1:]):
                        row_i = int(row[0])
                        self.assertAlmostEqual(dist, ref_dists[row_i][j+1], 3)
            # Sanity check 6
            if not is_spagedi:
                self.assertEqual(i+1, len(row))
            # Sanity check 8
            # (using reference matrix, which we already verified is the same
            # as the matrix calculated by DistanceMatrix.py, in check 7)
            ref_matrix = [dist.values() for row, dist in ref_dists.items()]
            ref_matrix_transpose = map(list, zip(*ref_matrix))
            self.assertEqual(ref_matrix, ref_matrix_transpose)

    def testDistanceMatrixAvailable(self, method=DistanceMatrix):
        self.assertTrue('main' in vars(method))

    def testDistanceMatrixRunSmall(self, method=DistanceMatrix):
        parameters = {
            'input_fc': self.input_fc,
            'dist_unit': 'Kilometers',
            'matrix_type': 'square',
            'output_matrix': self.output_dists
        }

        method.main(mode='script', **parameters)

         # first, gather up our geographiclib based distance matrix
        ref_dists = self.geographiclibDistances(self.input_fc)

        # all the actual assertions happen within the comparison function
        self.compareDistances(ref_dists, self.output_dists)

    def testDistanceMatrixRunArcObjects(self, method=DistanceMatrix):
        parameters = {
            'input_fc': self.input_fc,
            'dist_unit': 'Kilometers',
            'matrix_type': 'square',
            'force_cpp': True, # force our ArcObjects code to execute
            'output_matrix': self.output_dists
        }

        method.main(mode='script', **parameters)

         # first, gather up our geographiclib based distance matrix
        ref_dists = self.geographiclibDistances(self.input_fc)

        # all the actual assertions happen within the comparison function
        self.compareDistances(ref_dists, self.output_dists)

    def testDistanceMatrixRunArcObjectsSpagedi(self, method=DistanceMatrix):
        parameters = {
            'input_fc': self.input_fc,
            'dist_unit': 'Kilometers',
            'matrix_type': 'spagedi',
            'force_cpp': True, # force our ArcObjects code to execute
            'output_matrix': self.output_dists
        }

        method.main(mode='script', **parameters)

        with open(self.output_dists, 'rU') as dists:
            lines = dists.readlines()
            header = lines[0].split("\t")
            self.assertEqual(len(header), 19)
            self.assertEqual(header[0], 'M17')

        # first, gather up our geographiclib based distance matrix
        ref_dists = self.geographiclibDistances(self.input_fc)

        # all the actual assertions happen within the comparison function
        self.compareDistances(ref_dists, self.output_dists, True)

    def testToolboxImport(self):
        self.toolbox = arcpy.ImportToolbox(consts.pyt_file)
        self.assertTrue('DistanceMatrix' in vars(self.toolbox))

    def tearDown(self):
        if os.path.exists(self.output_dists):
            # clean up from any past runs
            arcpy.Delete_management(self.output_dists)

class TestShortestDistancePaths(unittest.TestCase):
    """ Test the shortest distance path script works, with
        a shapefile output."""

    def setUp(self):
        self.input_fc = fgdb.input_fc_mem
        self.output_fc = os.path.join(fgdb.dir_path, 'Test_ShortestDistancePaths')
        self.shape_fn = "{}.shp".format(self.output_fc)

    def testShortestDistancePathsAvailable(self, method=ShortestDistancePaths):
        self.assertTrue('main' in vars(method))

    def testShortestDistancePathsRun(self, method=ShortestDistancePaths):
        parameters = {
            'input_fc': self.input_fc,
            'output_fc': self.output_fc,
        }
        method.main(mode='script', **parameters)

        output_file_extensions = ('.cpg', '.dbf', '.prj', '.sbn',
                                  '.sbx', '.shp', '.shp.xml', '.shx')
        for ext in output_file_extensions:
            self.assertTrue(arcpy.Exists(self.output_fc + ext))

        # test that a sample value matches expected values
        output_columns = [f.name for f in arcpy.ListFields(self.shape_fn)]
        fields = ('ID', 'Source_ID', 'Dest_ID', 'Distance_i')
        where = '"ID" = 272'
        with arcpy.da.SearchCursor(self.shape_fn, fields, where) as cursor:
            (fid, source_id, dest_id, dist_m) = cursor.next()
            self.assertEqual(source_id, 17.0)
            self.assertEqual(dest_id, 8.0)
            self.assertAlmostEqual(dist_m, 3173.9605395)

    def testToolboxImport(self):
        self.toolbox = arcpy.ImportToolbox(consts.pyt_file)
        self.assertTrue('ShortestDistancePaths' in vars(self.toolbox))

    def tearDown(self):
        if os.path.exists(self.shape_fn):
            arcpy.Delete_management(self.shape_fn)

class TestIndividualPaths(unittest.TestCase):
    """Individual paths -- make a set of paths for selected individuals."""

    def setUp(self):
        self.input_fc = fgdb.input_fc_mem
        self.output_fc = os.path.join(fgdb.path, 'Test_IndividualPaths')

    def testShortestDistancePathsAvailable(self, method=IndividualPaths):
        self.assertTrue('main' in vars(method))

    def testShortestDistancePathsRun(self, method=IndividualPaths):
        parameters = {
            'input_fc': self.input_fc,
            'output_name': self.output_fc,
        }
        method.main(mode='script', **parameters)

        self.assertTrue(arcpy.Exists(self.output_fc))

        # test that a sample value matches expected values
        output_columns = [f.name for f in arcpy.ListFields(self.output_fc)]
        fields = ('Individual_ID', 'From_Point', 'To_Point', 'StartDate', 'EndDate',
                'Distance_km')

        with arcpy.da.SearchCursor(self.output_fc, fields) as cursor:
            (iid, from_pt, to_pt, start_date, end_date, dist) = cursor.next()
            self.assertEqual(iid, 115)
            self.assertEqual(from_pt, 16)
            self.assertEqual(to_pt, 17)
            self.assertEqual(start_date, datetime.datetime(2004, 2, 20, 8, 49))
            self.assertEqual(end_date, datetime.datetime(2004, 2, 20, 9, 15))
            self.assertEqual(dist, 0.0)

        arcpy.Delete_management(self.output_fc)
        self.assertFalse(arcpy.Exists(self.output_fc))

    def testToolboxImport(self):
        self.toolbox = arcpy.ImportToolbox(consts.pyt_file)
        self.assertTrue('MakeIndividualPaths' in vars(self.toolbox))


class TestExtractRasterValuesToPoints(unittest.TestCase):

    def setUp(self):
        self.input_fc = fgdb.input_fc_mem
        self.input_full_fc = consts.test_fgdb_fc
        self.input_raster = consts.test_fgdb_raster
        self.raster_col = 'R_etopo1_downsampled_clipped'

    def testExtractRasterValuesToPointsAvailable(self, \
            method=ExtractRasterValuesToPoints):
        self.assertTrue('main' in vars(method))

    def testExtractRasterValuesToPointsNoInterpRun(self, \
            method=ExtractRasterValuesToPoints):
        # do this computation on an in-memory dataset,
        # we don't want to modify the source data.
        desc = arcpy.Describe(self.input_fc)
        self.assertEqual(desc.dataType, 'FeatureClass')
        parameters = {
            'input_raster': self.input_raster,
            'selected_layer': self.input_fc,
            'interpolate': False
        }
        method.main(mode='script', **parameters)

        columns = [f.name for f in arcpy.ListFields(self.input_fc)]
        self.assertTrue(self.raster_col in columns)

        with arcpy.da.SearchCursor(self.input_fc, self.raster_col) as cursor:
            raster_value = cursor.next()[0]
            self.assertEqual(raster_value, -15)

    def testExtractRasterValuesToPointsInterpRun(self, \
            method=ExtractRasterValuesToPoints):
        # do this computation on an in-memory dataset,
        # we don't want to modify the source data.
        desc = arcpy.Describe(self.input_fc)
        self.assertEqual(desc.dataType, 'FeatureClass')
        parameters = {
            'input_raster': self.input_raster,
            'selected_layer': self.input_fc,
            'interpolate': True
        }
        method.main(mode='script', **parameters)

        columns = [f.name for f in arcpy.ListFields(self.input_fc)]
        self.assertTrue(self.raster_col in columns)

        with arcpy.da.SearchCursor(self.input_fc, self.raster_col) as cursor:
            raster_value = cursor.next()[0]
            self.assertEqual(raster_value, -15)

    def testToolboxImport(self):
        self.toolbox = arcpy.ImportToolbox(consts.pyt_file)
        self.assertTrue('ExtractRasterByPoints' in vars(self.toolbox))

# export data tools
#

class TestExportToSRGD(unittest.TestCase):

    def setUp(self):
        self.input_fc = fgdb.input_fc_mem
        self.output_csv = os.path.join(fgdb.dir_path, 'to_srgd.csv')

    def testExportToSRGDAvailable(self, method=ExportToSRGD):
        self.assertTrue('main' in vars(method))

    def testExportToSRGDRun(self, method=ExportToSRGD):

        desc = arcpy.Describe(self.input_fc)
        self.assertEqual(desc.dataType, 'FeatureClass')
        parameters = {
            'input_fc': self.input_fc,
            'output_csv': self.output_csv
        }
        method.main(mode='script', **parameters)

        self.assertTrue(os.path.exists(self.output_csv))

        expected_header = ['Sample_ID', 'Individual_ID', 'Latitude', 'Longitude',
                'Date_Time', 'Region', 'Sex', 'Haplotype', 'L_GATA417_1',
                'L_GATA417_2', 'L_Ev37_1', 'L_Ev37_2', 'L_Ev96_1', 'L_Ev96_2',
                'L_rw4_10_1', 'L_rw4_10_2', 'Date_formatted']
        expected_data = ['1', '100', '11.0253', '-85.9176', '2005-03-09T11:39:00',
                'Cent America', 'M', 'E1', '206', '222', '208', '220', '157', '163',
                '196', '198', '2005-03-09T11:39:00']

        with open(self.output_csv, 'r') as f:
            csv_in = csv.reader(f)
            header = csv_in.next()
            self.assertEqual(header, expected_header)
            row = csv_in.next()
            self.assertEqual(row, expected_data)

    def testToolboxImport(self):
        self.toolbox = arcpy.ImportToolbox(consts.pyt_file)
        self.assertTrue('ExportSRGD' in vars(self.toolbox))

class TestExportToAIS(unittest.TestCase):

    def setUp(self):
        self.input_features = fgdb.input_fc_mem
        self.output_coords = os.path.join(fgdb.dir_path, 'coords.txt')
        self.output_genetics = os.path.join(fgdb.dir_path, 'genetics.txt')

    def testExportToAISAvailable(self, method=ExportToAIS):
        self.assertTrue('main' in vars(method))

    def testExportToAISRun(self, method=ExportToAIS):

        desc = arcpy.Describe(self.input_features)
        self.assertEqual(desc.dataType, 'FeatureClass')
        parameters = {
            'input_features': self.input_features,
            'id_field': 'Individual_ID',
            'output_coords': self.output_coords,
            'output_genetics': self.output_genetics
        }
        method.main(mode='script', **parameters)

        self.assertTrue(os.path.exists(self.output_coords))
        self.assertTrue(os.path.exists(self.output_genetics))

        with open(self.output_coords, 'r') as f:
            csv_in = csv.reader(f)
            self.assertEqual(csv_in.next(), ['100', '11.0253', '-85.9176'])
            self.assertEqual(csv_in.next(), ['101', '13.7851', '-90.2733'])

        with open(self.output_genetics, 'r') as f:
            csv_in = csv.reader(f)
            header = csv_in.next()
            self.assertEqual(header, ['4'])
            self.assertEqual(csv_in.next(),
                    ['100', '206\\222', '208\\220', '157\\163', '196\\198'])

    def testToolboxImport(self):
        self.toolbox = arcpy.ImportToolbox(consts.pyt_file)
        self.assertTrue('ExportAllelesInSpace' in vars(self.toolbox))

class TestExportToGenAlEx(unittest.TestCase):

    def setUp(self):
        self.input_fc = fgdb.input_fc_mem
        self.input_fc_nulls = 'in_memory/input_fc_nulls'
        self.output_name = os.path.join(fgdb.dir_path, 'to_genalex.csv')

    def testExportToGenAlExAvailable(self, method=ExportToGenAlEx):
        self.assertIn('main', vars(method))

    def testExportToGenAlExRun(self, method=ExportToGenAlEx):

        desc = arcpy.Describe(self.input_fc)
        self.assertEqual(desc.dataType, 'FeatureClass')

        # update the data to set the first two values to NULL to test that 
        # NULLs are encoded correctly by GenAlEx (i.e. treated as 0).
        arcpy.CopyFeatures_management(self.input_fc, self.input_fc_nulls)
        fields = ['Sample_ID', 'L_rw4_10_1', 'L_rw4_10_2']
        with arcpy.da.UpdateCursor(self.input_fc_nulls, fields, "Sample_ID = 3") as cursor:
            # should be one result with this case
            row = cursor.next()
            row[1] = None
            row[2] = None
            cursor.updateRow(row)

        parameters = {
            'input_features': self.input_fc_nulls,
            'id_field': 'Individual_ID',
            'order_by': 'Region',
            'output_name': self.output_name,
        }

        method.main(mode='script', **parameters)
        self.assertTrue(os.path.exists(self.output_name))

        with open(self.output_name, 'r') as f:
            csv_in = csv.reader(f, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)

            # size row: # loci, # samp, # pops, sz pop1, sz pop2, sz pop 3, sz pop4
            self.assertEqual(csv_in.next(), ['4','17','4','7','2','5','3'])
            # regions
            self.assertEqual(csv_in.next(), ['','','','Cent America', 'CA_OR', 'Mexico AR', 'Mexico Main'])
            # header
            self.assertEqual(csv_in.next(), ['Individual_ID', 'Region', 'GATA417',
                '', 'Ev37', '', 'Ev96', '', 'rw4_10', '', '', 'Latitude', 'Longitude',
                'Sample_ID', 'Date_Time', 'Sex', 'Haplotype', 'Date_formatted']) 

            # skip to last row
            csv_in.next()
            csv_in.next()
            # the values for the rw4_10 haplotype should both be '0', which is
            # how GenAlEx handles NULL values.
            self.assertEqual(csv_in.next(), ['102', 'Cent America', '207', '221',
                '194', '198', '161', '163', '0', '0', '', '8.708', '-83.7341',
                '3', '2004-01-23T10:31:00', 'U', '0', '2004-01-23 10:31:00'])

    def testToolboxImport(self):
        self.toolbox = arcpy.ImportToolbox(consts.pyt_file)
        self.assertIn('ExportGenAlEx', vars(self.toolbox))

class TestExportToGenepop(unittest.TestCase):

    def setUp(self):
        self.input_fc = fgdb.input_fc_mem
        #self.input_fc = consts.test_fgdb_tiny_fc
        self.output_name = os.path.join(fgdb.dir_path, 'to_genepop.txt')

    def testExportToGenepopAvailable(self, method=ExportToGenepop):
        self.assertIn('main', vars(method))

    def testExportToGenepop(self, method=ExportToGenepop):
        desc = arcpy.Describe(self.input_fc)
        self.assertEqual(desc.dataType, 'FeatureClass')
        parameters = {
            'input_features': self.input_fc,
            'id_field': 'Individual_ID',
            'order_by': 'Region',
            'output_name': self.output_name,
        }

        method.main(mode='script', **parameters)
        self.assertTrue(os.path.exists(self.output_name))

        columns = ['GATA417', 'Ev37', 'Ev96', 'rw4_10', 'Haplotype']
        with open(self.output_name, 'rU') as f:
            lines = f.readlines()

            # this file is plain text, has a comment row, a header row, then a
            # line labeled 'pop' followed by all records of that population, with
            # another 'pop' designating a new population.
            for (i, raw_line) in enumerate(lines):
                line = raw_line.strip()
                # header
                if i == 1:
                    self.assertEqual(line.split(","), columns)

                # first 'pop' identified
                if i == 2:
                    self.assertEqual(line.lower(), 'pop')

                # first data row
                if i == 3:
                    row = line.split(",")
                    label = row[0].strip()
                    self.assertEqual(label, '100-Cent_America')

                    expected = ['206222', '208220', '157163', '196198', '002']
                    data = row[1].strip().split(" ")
                    # all values but last are diploid loci
                    for (j, col) in enumerate(data):
                        self.assertEqual(col, expected[j])

    def testToolboxImport(self):
        self.toolbox = arcpy.ImportToolbox(consts.pyt_file)
        self.assertIn('ExportGenepop', vars(self.toolbox))


# this test should be run after a fresh run of makeaddin to rebuild the .esriaddin file.
class TestAddin(unittest.TestCase):
    def setUp(self):
        self.addin_path = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', 'genegis.esriaddin'))
        self.addin_zip = zipfile.ZipFile(self.addin_path, 'r')
        self.names = self.addin_zip.namelist()

    def testToolboxIsPresent(self):
        toolbox_path = 'Install/toolbox/genegis.pyt'
        self.assertIn(toolbox_path, self.names)

    def testClassifedImportIsPresent(self):
        import_path = 'Install/toolbox/scripts/ClassifiedImport.py'
        self.assertIn(import_path, self.names)

    def testGeodesicDllIsPresent(self):
        dll_path = 'Install/toolbox/lib/geodesic/geodesic.dll'
        self.assertIn(dll_path, self.names)

if __name__  == '__main__':
    unittest.main()
    # we aren't using the context manager here, so manually delete our fgdb.
    del(fgdb)


