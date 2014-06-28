# distance_comparison.py: a testing companion script to DistanceMatrix.py which 
# compares between the high-speed geodesic form and the ArcPy based version.
import arcpy
import ctypes
import os
import sys

import utils

from DistanceMatrix import run_geodesic_gp

def load_geodesic_dll():
    fn = None
    # load the DEBUG build of the DLL.
    dll_path = os.path.abspath( \
        os.path.join(os.path.abspath(os.path.dirname(__file__)), \
        '..', 'arcobjects', 'geodesic', 'Debug', 'geodesic.dll'))

    if os.path.exists(dll_path):
        try:
            loaded_dll = ctypes.cdll.LoadLibrary(dll_path)
        except Exception as e:
            msg = "Failed to load high-speed geodesic library."
            utils.msg(msg, mtype='error', exception=e)
            return None
        fn = loaded_dll.CalculatePairwiseGeodesicDistances
        fn.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_double]
        fn.restype = ctypes.c_int
    return fn

input_fc = os.path.abspath(os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    '..', '..', '..', 'tests', 'data', 
    'test.gdb', 'SRGD_tiny_Spatial'))

output_matrix = os.path.abspath(os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    '..', '..', '..', 'tests', 'data', 
    'dists_sample.csv'))

output_matrix_gp = os.path.abspath(os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    '..', '..', '..', 'tests', 'data', 
    'dists_sample_gp.csv'))

geodesic_cpp_fn = load_geodesic_dll()
if geodesic_cpp_fn is not None:
    desc = arcpy.Describe(input_fc)
    # To run this, we need the full path to the input, not just the
    # short one handed to us.
    input_fc_fullpath = os.path.join(desc.path, desc.file)

    utils.msg("Loaded high-performance geodesic calculations, running...")
    returncode = geodesic_cpp_fn(input_fc_fullpath, output_matrix, 1, 1)
    if returncode == -1:
        utils.msg("Cannot open the output file.", mtype='error')
    elif returncode == -2:
        utils.msg("Cannot open the input file.", mtype='error')
    elif returncode == -3:
        utils.msg("The input matrix is too large! consider" + \
                "subsetting your results.", mtype='error')
    elif returncode == -3:
        utils.msg("This tool requires point features as input.", \
                mtype='error')
    elif returncode == 0:
        utils.msg("Distance matrix calculations complete.")
    else:
        utils.msg("Unknown failure occured in high-performance " + \
                "geodesic module.", mtype='error')

    if returncode != 0:
        sys.exit()

# run the gp version for comparison
utils.msg("Running the GP version...")
run_geodesic_gp(input_fc, 1, output_matrix_gp, 3, False)
