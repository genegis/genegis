import os
import sys
import unittest

import arcpy
import zipfile

from tempdir import TempDir

import consts
import utils

# import our local directory so we can use the internal modules
import_paths = ['../Install/toolbox', '../Install']
utils.addLocalPaths(import_paths)

from scripts import ClassifiedImport

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
