import os
import sys

import arcpy
import pythonaddins

# enable local imports
local_path = os.path.dirname(__file__)
sys.path.insert(0, local_path)

# import local settings
import config

def toolDialog(toolbox, tool):
    """Error-handling wrapper around pythonaddins.GPToolDialog."""
    result = None
    try:
        result = pythonaddins.GPToolDialog(toolbox, tool)
        # FIXME: this is a hack to prevent:
        # TypeError: GPToolDialog() takes at most 1 argument (2 given)
        print '', 
    except TypeError:
        print "recieved TypeError when trying to run GPToolDialog(" + \
            "{toolbox}, {tool}))".format(toolbox=toolbox, tool=tool)
    # don't return anything. this prevents:
    #   TypeError: GPToolDialog() takes at most 1 argument (2 given)
    return result

def selectedLayer():
    # return the selected layer object, check that it's just points
    layer = None
    if config.selected_layer:
        # our preference is to always use the selected_layer object, which is
        # populated by our combination box.
        layer = config.selected_layer
    else:
        # if no layer is set, default to the current layer in the TOC
        layer = pythonaddins.GetSelectedTOCLayerOrDataFrame()

    #try:
    desc = arcpy.Describe(layer)
    #except:
    #    pass
    if layer is None or desc.datasetType not in config.allowed_formats:
        msg = "No layer selected! Please select a point layer from the table of contents."
        title = "No selected layer"
        pythonaddins.MessageBox(msg, title)
    else:
        if desc.shapeType not in config.allowed_types:
            msg = "Selected layer doesn't contain points."
            title = "No points in layer"
            pythonaddins.MessageBox(msg, title)
            layer = None
        # set our default SRID based on the input data layer
        config.sr = desc.spatialReference
    return layer

def currentLayers():
    # find layers in current map document
    layers = []
    # inspect the layer list, find the first point layer
    mxd = arcpy.mapping.MapDocument("current")
    # get a list of all layers, store it
    config.all_layers = arcpy.mapping.ListLayers(mxd)

    # iterate over our layers, find those which are candidates for analysis
    if config.all_layers is not None:
        for layer in config.all_layers
            try:
                # FIXME: check performance on this. if expensive, do something cheaper
                desc = arcpy.Describe(layer)
                if desc.datasetType in config.allowed_formats and \
                    desc.shapeType in config.allowed_types:
                    layers.append(layer)
            except:
                # silently skip layers which don't support describe (e.g. AGOL).
                continue
    return layers

def getLayerByName(name):
    named_layer = None
    for layer in currentLayers():
        if layer.name == name:
            named_layer = layer
    return named_layer 

def extentPolygon(extent, source_layer=None):
    polygon_extent = None

    if extent:
        if source_layer:
            # extract the spatial reference from the source layer
            desc = arcpy.Describe(source_layer)
            sr = desc.spatialReference
        else:
            # use default spatial reference
            sr = config.sr

        # extract the coordinates from our extent object
        coords = [[extent.XMin,extent.YMin],[extent.XMax,extent.YMin], \
                    [extent.XMax,extent.YMax],[extent.XMin,extent.YMax]]

        # convert it to a polygon, we need this to compute the intersection
        polygon_extent = arcpy.Polygon(arcpy.Array(
            [arcpy.Point(x,y) for x,y in coords]), sr)

    return polygon_extent

def selectIndividuals(output_feature, display=False):
    res = {}
    fields = [f.name for f in arcpy.ListFields(output_feature)]
    if config.id_field in fields:
        cur = arcpy.da.SearchCursor(output_feature, (config.id_field))
        individuals = [row[0] for row in cur]
        unique_individuals = set(individuals)
        res = {'indiv' : individuals, 'unique' : unique_individuals}
        if display == True:
            msg = "Samples: {0}, Unique Individuals: {1}".format(
                    len(individuals), len(unique_individuals))
            title = "Samples found in selection"
            pythonaddins.MessageBox(msg, title)
    else:
        print "Couldn't find an individual ID field!"

    return res

def intersectFeatures(input_feature, intersect_feature, output_feature):
    # perform an intersection. Can take an optional 'add to selection' vs. 'new selection'
    selection_results = arcpy.SelectLayerByLocation_management(
            input_feature, "INTERSECT", intersect_feature)

    # overwrite outputs
    if arcpy.Exists(output_feature):
        arcpy.Delete_management(output_feature)

    # FIXME: expose the TOC on / off to the user
    add_output = arcpy.env.addOutputsToMap
    arcpy.env.addOutputsToMap = False
    # copy features to our output feature
    arcpy.CopyFeatures_management(selection_results.getOutput(0), output_feature)
    arcpy.env.addOutputsToMap = add_output

    return output_feature
