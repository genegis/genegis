# DistanceMatrix.py: geodesic distances between points
# -*- coding: utf-8 -*-
# Created by: Shaun Walbridge
#             Esri

# Created on: 26 May 2013
# Full distance matrix between all elements.

import arcpy
import os
import sys
from collections import OrderedDict

# local imports
import utils
import config

def main(input_fc=None, dist_unit=None, output_matrix=None, mode=config.settings.mode):
    
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

    # yes, all this mucking about is necessary to get a row count
    row_count = int(arcpy.GetCount_management(input_fc_mem).getOutput(0))
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
                    # TODO: Each Polyline initialization must pay the COM object gods, and ends up
                    # making this much more expensive than AO C++ or even comtypes calls, evalaute rewriting.
                    line = arcpy.Polyline(arcpy.Array([p1, p2]), sr)
                    # distance, always returned in meters, scale by our expected result units.
                    dist = line.getLength("GEODESIC") * unit_factor
                    # if the units aren't meters, convert as needed
                    
            distance_matrix[fid][to_fid] = dist
    print "Distance matrix calculations complete."

    # FIXME: generate it as a CSV file, then do TableToTable to pull it back in if requested.

    # Now compute the lines between these locations.
    try:
        # copy the final result back to disk.
        utils.msg("Writing results to disk…")
    
        with open(output_matrix, 'w') as csv:
            csv.write(",%s\n" % ",".join([str(s) for s in distance_matrix.keys()]))
            for (fid, row) in distance_matrix.items():
                csv.write("{0},{1}\n".format(fid, ",".join([str(s) for s in row.values()])))

        utils.msg("Created distance matrix successfully: {0}".format(output_matrix))
    except Exception as e:
        utils.msg("Error creating distance matrix.", mtype='error', exception=e)
        sys.exit()

# when executing as a standalone script get parameters from sys
if __name__=='__main__':

    # Defaults when no configuration is provided
    # TODO: change these to be test-based.
    defaults_tuple = (
        ('input_fc', ""),
        ('output_matrix', "TestFC"),
    )

    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(mode='script', **defaults)
