import os
import sys

import arcpy
import pythonaddins

# enable local imports
addin_path = os.path.dirname(__file__)
sys.path.insert(0, addin_path)

# import local settings
import config
import utils

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

    def __init__(self, display=True):
        self.enabled = True
        # XXX: If needed, this tool could be swapped to a combobox class, then 
        # the 'shape' and 'cursor' can be set based on the selection type.
        self.shape = "RECTANGLE"
        self.cursor = 3 # the 'crosshair'
        self._extent = None
        # display controls whether this tool does its reporting,
        # or just passes on its results silently.
        self.display = display

    def onCircle(self, circle_geometry):
        pass

    def onRectangle(self, rectangle_geometry):
        extent = rectangle_geometry
        polygon_extent = utils.extentPolygon(extent)
        # the current _selected_ layer in ArcMap
        layer = utils.selectedLayer()
        if layer is None:
            return None

        # perform an intersection. Can take an optional 'add to selection' vs. 'new selection'
        selection_results = arcpy.SelectLayerByLocation_management(
                layer.name, "INTERSECT", polygon_extent)

        # store the results in memory, no need to bring spindles into this
        output_feature = 'in_memory/primary_selection_points'
        if arcpy.Exists(output_feature):
            arcpy.Delete_management(output_feature)

        # FIXME: expose the TOC on / off to the user
        arcpy.env.addOutputsToMap = False
        arcpy.CopyFeatures_management(selection_results.getOutput(0), output_feature)
        arcpy.env.addOutputsToMap = True
        
        utils.selectIndividuals(output_feature, self.display)

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
        self.shape = "Rectangle"
        self.cursor = 3 # the 'crosshair'
        self._extent = None

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
            config.selected_layer = utils.getLayerByName(selection)
            # FIXME: check how much memory the object will soak up 
            # prior to loading
            config.selected_object = None
            print config.selected_layer
        pass
    def onFocus(self, focused):
        # update the layer list _only_ on focus events, preventing this from
        # being triggered on the addin startup.
        if focused:
            self.layers = utils.currentLayers()
            if len(self.layers) > 0:
                self.items = [l.name for l in self.layers]
            else:
                print "no layers."
    def onEnter(self):
        pass
    def refresh(self):
        pass
