import os
import sys

import arcpy
import pythonaddins

# enable local imports
addin_path = os.path.dirname(__file__)
sys.path.insert(0, addin_path)

# import local settings
import config

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

    if layer is None:
        msg = "No layer selected! Please select a point layer from the table of contents."
        title = "No selected layer"
        pythonaddins.MessageBox(msg, title)
    else:
        desc = arcpy.Describe(layer)
        geom_type = desc.shapeType
        if geom_type not in config.allowed_types:
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
    raw_layers = arcpy.mapping.ListLayers(mxd)
    if raw_layers is not None:
        for layer in raw_layers:
           # FIXME: check performance on this. if expensive, do something cheaper
            desc = arcpy.Describe(layer)
            if desc.shapeType in config.allowed_types:
                layers.append(layer)
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
        res = {'individuals' : individuals, 'unique_individuals' : unique_individuals}
        if display == True:
            msg = "Samples: {0}, Unique Individuals: {1}".format(
                    len(individuals), len(unique_individuals))
            title = "Samples found in selection"
            pythonaddins.MessageBox(msg, title)
    else:
        print "Couldn't find an individual ID field!"

    return res
