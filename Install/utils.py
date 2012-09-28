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
