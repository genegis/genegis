# IndividualPaths.py

import arcpy
import os
import sys
# local imports
import utils
import config
import time

add_outputs = arcpy.env.addOutputsToMap
arcpy.env.addOutputsToMap = True
arcpy.env.overwriteOutput = True

def main(selected_pts=None, source_fc=None, output_name=None):
    # get the spatial reference of input
    desc = arcpy.Describe(selected_pts)
    sr = desc.spatialReference

    # get list of Inividual_IDs from selected_pts

    #utils.msg("Getting list of Individuals")
    with arcpy.da.SearchCursor(selected_pts, config.settings.id_field) as cur:
        # write cursor to a list
        all_ids = [row[0] for row in cur if row[0] is not None]

    # eliminate duplicate IDs
    indiv_sort = sorted(set(all_ids))
    #format list for a SQL WHERE clause
    individuals = tuple(indiv_sort)

    out_path = os.path.dirname(output_name)
    out_name = os.path.basename(output_name)

    geometry_type = 'POLYLINE'
    template = ""
    has_m = 'DISABLED'
    has_z = 'DISABLED'
    # create the new FeatureClass
     
    layer = arcpy.CreateFeatureclass_management(out_path, out_name,
            geometry_type, template, has_m, has_z, sr)
    if not arcpy.Exists(layer):
        #utils.msg("Layer not created for some reason?")
        #sys.exit()
        pass
    # field list for insert cursor
    f_names = []
    f_names.append("SHAPE@")
    # default fields: "OID", "Shape"
    # fields for AddFields
    f_list = [('From_Point', 'LONG'),
              ('To_Point','LONG'),
              ('StartDate','DATE'),
              ('EndDate','DATE'),
              ('Individual_ID','LONG'),
              ('Distance_km','DOUBLE'),
              ('Elapsed_days','DOUBLE')]
    # add the required fields
    for f_name, f_type in f_list:
        arcpy.AddField_management(layer, f_name, f_type)
        f_names.append(f_name)
    # open an insert cursor for the new layer
    ins_cursor = arcpy.da.InsertCursor(layer, f_names)

    # open search cursor to find all Encounters for the identified individuals
    fields = ["OBJECTID", "SHAPE@XY", "Individual_ID", "Date_Formatted"]
    #sql_where = 'Individual_ID IN ' + str(individuals)
    sql_order = (None, 'ORDER BY "Individual_ID", "Date_Formatted"')
    sql_where = ""
    explode = False
    with arcpy.da.SearchCursor(source_fc, fields, sql_where, sr, explode,
                                sql_order) as id_cursor:
        row = id_cursor.next()
        # store first row values
        from_id = row[0]
        individual = row[2]
        from_date = row[3]
        # create a point from row geometry
        this_point = arcpy.Point(row[1][0],row[1][1])
        # create array to hold pairs of points
        array = arcpy.Array(this_point)
        # iterate over reamining rows
        for row in id_cursor:
            if row[2] == individual:
                this_point = arcpy.Point(row[1][0],row[1][1])
                array.add(this_point)
                # construct a path using the two points in the array
                segment = arcpy.Polyline(array, sr, False, False)
                # update values for new row
                to_id = row[0]
                to_date = row[3]
                new_date = to_date
                #dist, elapsed = utils.calc_distance(segment, from_date, to_date)
                dist = segment.getLength("GEODESIC")/1000.0
                delta = to_date - from_date
                elapsed = (delta.days)+(delta.seconds/3600.0)
                # add path to feature class
                ins_cursor.insertRow([segment, from_id, to_id, from_date, to_date,
                                      individual, dist, elapsed])
                # remove "from" point
                array.remove(0)
                individual = row[2]
                from_id = to_id
                from_date = to_date
            else:
                # skip unused
                if row[2] not in individuals:
                    continue
                # change of Individual, initiate a new line
                from_id = row[0]
                this_point = arcpy.Point(row[1][0],row[1][1])
                # empty array
                array.remove(0)
                array.add(this_point)
                individual = row[2]
                from_date = row[3]
        # end for row in id_cursor
    # end with id_cursor
    # TODO: apply symbology?
    
    # restore add outputs state
    arcpy.env.addOutputsToMap = add_outputs

# when executing as a standalone script get parameters from sys
if __name__ == '__main__':
    # Defaults when no configuration is provided
    defaults_tuple = (
        ('selected_pts', "C:\\geneGIS\\WorkingFolder\\geneGISv8.gdb\\Selection"),
        ('source_fc', "C:\\geneGIS\\WorkingFolder\\geneGISv8.gdb\\Encounter"),
        ('output_name', "TestPath")
    )
    defaults = utils.parameters_from_args(defaults_tuple, sys.argv)
    main(mode='script', **defaults)
    main(**defaults)
     #main(selected_pts, source_fc, output_name)
