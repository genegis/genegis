# DistanceMatrix.py: geodesic distances between points
# -*- coding: utf-8 -*-
# Created by: Shaun Walbridge
#             Esri

# Created on: 26 May 2013
# Full distance matrix between all elements.

import arcpy
import os
import sys
import ctypes
from collections import OrderedDict

# local imports
import utils
import config

def main(input_fc=None, dist_unit=None, matrix_type=None, output_matrix=None, mode=config.settings.mode):
   
    # does the input fc exist?
    if not arcpy.Exists(input_fc):
        utils.msg("Input, %s, doesn't exist.", mtype='error')
        sys.exit()

    # determine appropriate unit conversion factor.
    if not config.distance_units.has_key(dist_unit):
        utils.msg("Invalid distance units detected: `{0}`".format(dist_unit))
        sys.exit()
    else:
        utils.msg("Output units: {0}".format(dist_unit))
        (unit_abbr, unit_name, unit_factor) = config.distance_units[dist_unit]

    if matrix_type == 'Square':
        is_spagedi = False
    elif matrix_type == 'Square (SPAGeDi formatted)':
        is_spagedi = True
    else:
        is_spagedi = False

    # yes, all this mucking about is necessary to get a row count
    row_count = int(arcpy.GetCount_management(input_fc).getOutput(0))
 
    geodesic_cpp_fn = load_geodesic_dll()
    if geodesic_cpp_fn is not None and row_count > 50:
        if is_spagedi:
            utils.msg("Unable to compute SPAGeDi compatible matrix for large datasets,  to be fixed.")
            sys.exit()

        # TODO: handle units in the CPP version.
        utils.msg("Loaded high-performance geodesic calculations, running…")
        returncode = geodesic_cpp_fn(input_fc, output_matrix)
        if returncode == -1:
            utils.msg("Cannot open the output file.")
        elif returncode == -2:
            utils.msg("Cannot open the input file.")
        elif returncode == -3:
            utils.msg("The input matrix is too large! consider subsetting your results.")
        elif returncode == 0:
            utils.msg("Distance matrix calculations complete.")
        else:
            utils.msg("Unknown failure occured in high-performance geodesic module.")
    else:
        run_geodesic_gp(input_fc, unit_factor, output_matrix, row_count, is_spagedi)

    utils.msg("Created distance matrix successfully: {0}".format(output_matrix))

def load_geodesic_dll():
    fn = None
    dll_path = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "lib", "geodesic.dll"))
    if os.path.exists(dll_path):
        try:
            loaded_dll = ctypes.cdll.LoadLibrary(dll_path)
        except Exception as e:
            utils.msg("Failed to load high-speed geodesic library.")
            return None
        fn = loaded_dll.CalculatePairwiseGeodesicDistances
        fn.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        fn.restype = ctypes.c_int
    return fn                

def run_geodesic_gp(input_fc, unit_factor, output_matrix, row_count, is_spagedi):
    input_fc_mem = 'in_memory/input_fc'
    try:
        utils.msg("Copying features into memory…")
        arcpy.CopyFeatures_management(input_fc, input_fc_mem)
    except Exception as e:
        utils.msg("Unable to copy features into memory.", mtype='error', exception=e)
        sys.exit()

    # get the spatial reference of our input, determine the type
    desc = arcpy.Describe(input_fc_mem)
    sr = desc.spatialReference
    if sr.type not in ['Geographic', 'Projected']:
        utils.msg("This tools only works with geographic or projected data.", mtype='error')
        sys.exit()

    output_fc_mem = 'in_memory/output_fc'

    utils.msg("Finding all input points…")
    distance_matrix = OrderedDict()
    points = OrderedDict()
    records = arcpy.da.SearchCursor(input_fc_mem, ['OID@', 'SHAPE@XY'])
    for row in records:
        (fid, point) = row
        points[fid] = arcpy.Point(point[0], point[1])

    indicator = 0
    utils.msg("Computing distances…")
    for (fid, from_point) in points.items():
        pct_progress = int(fid / float(row_count)*100)
        if pct_progress > indicator:
            indicator = pct_progress
            utils.msg("{0}%".format(indicator))
        p1 = points[fid]
        distance_matrix[fid] = OrderedDict()
        for (to_fid, to_point) in points.items():
            if to_fid == fid:
                dist = 0
            elif distance_matrix.has_key(to_fid):
                # here, modeling a symmetrical matrix
                dist = distance_matrix[to_fid][fid]
            else:
                p2 = points[to_fid]
                if p1.equals(p2):
                    dist = 0
                else:
                    # Each Polyline initialization must pay the COM object gods, and ends up
                    # making this much more expensive than AO C++ or even comtypes calls.
                    line = arcpy.Polyline(arcpy.Array([p1, p2]), sr)
                    # distance, always returned in meters, scale by our expected result units.
                    dist = line.getLength("GEODESIC") * unit_factor
                    
            distance_matrix[fid][to_fid] = dist
    utils.msg("Distance matrix calculations complete.")

    # FIXME: generate it as a CSV file, then do TableToTable to pull it back in if requested.

    # Now compute the lines between these locations.
    try:
        # copy the final result back to disk.
        utils.msg("Writing results to disk…")
        # The specifics of the SPAGeDi matrix format are described in section 3.7 of the manual.
        if is_spagedi:
            first_header_cell = "M%i" % row_count
            sep = "\t"
        else:
            first_header_cell = ""
            sep = ","

        with open(output_matrix, 'w') as csv:
            # initialize with our header row 
            output_rows = [[first_header_cell] + [str(s) for s in distance_matrix.keys()]]
            for (fid, row) in distance_matrix.items():
                output_rows.append([str(fid)] + [str(s) for s in row.values()])
            for row in output_rows:
                csv.write("{0}\n".format(sep.join(row)))
            if is_spagedi:
                csv.write("END\n")

    except Exception as e:
        utils.msg("Error creating distance matrix.", mtype='error', exception=e)
        sys.exit()


# when executing as a standalone script get parameters from sys
if __name__=='__main__':

    # Defaults when no configuration is provided
    # TODO: change these to be test-based.
    defaults_tuple = (
        ('input_fc', ""),
        ('dist_unit', 'Kilometers'),
        ('matrix_type', 'Square'),
        ('output_matrix', "TestFC"),
    )

    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(mode='script', **defaults)
