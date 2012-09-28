import os
import sys

import arcpy
import pythonaddins

# enable local imports
addin_path = os.path.dirname(__file__)
sys.path.insert(0, addin_path)

# import local settings
import config

def _selectedLayer():
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
        if geom_type not in _allowedDataTypes():
            msg = "Selected layer doesn't contain points."
            title = "No points in layer"
            pythonaddins.MessageBox(msg, title)
            layer = None
    return layer

def _currentLayers():
    # find layers in current map document
    layers = []
    # inspect the layer list, find the first point layer
    mxd = arcpy.mapping.MapDocument("current")
    raw_layers = arcpy.mapping.ListLayers(mxd)
    print "_currentLayers: got %i layers" % len(raw_layers)
    if raw_layers is not None:
        for layer in raw_layers:
           # FIXME: check performance on this. if expensive, do something cheaper
            desc = arcpy.Describe(layer)
            if desc.shapeType in _allowedDataTypes():
                layers.append(layer)
    return layers

def _getLayerByName(name):
    named_layer = None
    for layer in _currentLayers():
        if layer.name == name:
            named_layer = layer
    return named_layer 

def _allowedDataTypes():
    return ["Point", "MultiPoint"]

class ButtonClass5(object):
    """Implementation for genegis_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

class ButtonClass6(object):
    """Implementation for genegis_addin.button_1 (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

class SummarizeEncounters(object):
    """Implementation for genegis_summarize.tool (Tool)."""

    def __init__(self):
        self.enabled = True
        # XXX: If needed, this tool could be swapped to a combobox class, then 
        # the 'shape' and 'cursor' can be set based on the selection type.
        self.shape = "RECTANGLE"
        self.cursor = 3 # the 'crosshair'
        self._extent = None

    def onCircle(self, circle_geometry):
        pass

    def onRectangle(self, rectangle_geometry):
        extent = rectangle_geometry
        # the current _selected_ layer in ArcMap
        layer = _selectedLayer()
        if layer is None:
            return None

       # extract the coordinates from our extent object
        coords = [[extent.XMin,extent.YMin],[extent.XMax,extent.YMin], \
                [extent.XMax,extent.YMax],[extent.XMin,extent.YMax]]

        # convert it to a polygon, we need this to compute the intersection
        polygon_extent = arcpy.Polygon(arcpy.Array(
            [arcpy.Point(x,y) for x,y in coords]), arcpy.SpatialReference(4326))

        # perform an intersection. Can take an optional 'add to selection' vs. 'new selection'
        selection_results = arcpy.SelectLayerByLocation_management(
                layer.name, "INTERSECT", polygon_extent)

        # store the results in memory, no need to bring spindles into this
        output_feature = 'in_memory/primary_selection_points'
        if arcpy.Exists(output_feature):
            arcpy.Delete_management(output_feature)
        arcpy.CopyFeatures_management(selection_results.getOutput(0), output_feature)

        # FIXME: this is currently hard-coded, needs to reflect the 'ID' 
        # column chosen during the import process.
        id_field = "Individual_ID"
        fields = [f.name for f in arcpy.ListFields(output_feature)]
        if id_field in fields:
            cur = arcpy.da.SearchCursor(output_feature, (id_field))
            individuals = [row[0] for row in cur]
            unique_individuals = set(individuals)
            msg = "Samples: {0}, Unique Individuals: {1}".format(len(individuals), len(unique_individuals))
            title = "Samples found in selection"
            pythonaddins.MessageBox(msg, title)
        else:
            print "Couldn't find an individual ID field!"
 
        """
        so we'd probably want to identify the specific columns of interest (haplotypes?),
        perhaps using a drop-down menu, and then use the select tool to generate our areas of
        interest, and shoot back out some summary statistics based on those observations.
        """

        # just a string representation of the feature name
        return output_feature

class CompareEncounters(object):
    """Implementation for genegis_compare.tool (Tool)"""
    def __init__(self):
        self.enabled = True
        self.shape = "NONE" # Can set to "Line", "Circle" or "Rectangle" for interactive shape drawing and to activate the onLine/Polygon/Circle event sinks.
    def onMouseDown(self, x, y, button, shift):
        pass
    def onMouseDownMap(self, x, y, button, shift):
        pass
    def onMouseUp(self, x, y, button, shift):
        pass
    def onMouseUpMap(self, x, y, button, shift):
        pass
    def onMouseMove(self, x, y, button, shift):
        pass
    def onMouseMoveMap(self, x, y, button, shift):
        pass
    def onDblClick(self):
        pass
    def onKeyDown(self, keycode, shift):
        pass
    def onKeyUp(self, keycode, shift):
        pass
    def deactivate(self):
        pass
    def onCircle(self, circle_geometry):
        pass
    def onLine(self, line_geometry):
        pass
    def onRectangle(self, rectangle_geometry):
        pass

class LayerCombo(object):
    """Implementation for genegis_layer_combo.combobox (Combobox)"""
    def __init__(self):
        self.layers = []
        self.items = ['genetic_points']
        self.editable = True
        self.enabled = True
        self.dropdownWidth = "WWWWWWW"
        self.width = "WWWWWWW"

    def onSelChange(self, selection):
        if selection:
            print "got a selection: %s; %s" % (type(selection), selection)
            config.selected_layer = _getLayerByName(selection)
            # FIXME: check how much memory the object will soak up 
            # prior to loading
            config.selected_object = None
            print config.selected_layer
        pass
    def onFocus(self, focused):
        # update the layer list _only_ on focus events, preventing this from
        # being triggered on the addin startup.
        if focused:
            self.layers = _currentLayers()
            if len(self.layers) > 0:
                self.items = [l.name for l in self.layers]
            else:
                print "no layers."
    def onEnter(self):
        pass
    def refresh(self):
        pass
