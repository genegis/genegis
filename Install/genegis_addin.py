import os
import sys

import arcpy
import pythonaddins

# enable local imports
local_path = os.path.dirname(__file__)
sys.path.insert(0, local_path)

# import local settings
import config
import utils

# get the paths for our toolboxes
imported_toolbox = os.path.join(local_path, "toolbox", "imported.tbx")
genegis_toolbox = os.path.join(local_path, "toolbox", "genegis.pyt")

#
# data management
#
class ImportData(object):
    """Implementation for genegis_import.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        utils.toolDialog(genegis_toolbox, "ClassifiedImport")

class ExportGenAlEx(object):
    """Implementation for genegis_export_genalex_codominant.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        utils.toolDialog(genegis_toolbox, "ExportGenAlEx")

class ExportKML(object):
    """Implementation for genegis_export_kml.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        utils.toolDialog("Conversion Tools", "LayerToKML")

#
# summarization tools
#

class ExtractValuesToPoints(object):
    """Implementation for genegis_extract_values_to_points.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        utils.toolDialog(genegis_toolbox, 'extractRasterByPoints')

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

    def onRectangle(self, rectangle_geometry):
        polygon_extent = utils.extentPolygon(rectangle_geometry)
        # the current _selected_ layer in ArcMap
        layer = utils.selectedLayer()
        if layer is None:
            return None

        # store the results in memory, no need to bring spindles into this
        output_feature = 'in_memory/primary_selection_points'
        utils.intersectFeatures(layer.name, polygon_extent, output_feature)

        # get the stats for our inviduals
        indiv_stats = utils.selectIndividuals(output_feature, self.display)
        """
        so we'd probably want to identify the specific columns of interest (haplotypes?),
        perhaps using a drop-down menu, and then use the select tool to generate our areas of
        interest, and shoot back out some summary statistics based on those observations.
        """

        results = {'indiv_stats': indiv_stats, 'output_feature': output_feature}
       
        # push results to a shared variable
        config.primary_results = results
        return results

class CompareEncounters(object):
    """Implementation for genegis_compare.tool (Tool)"""
    def __init__(self, display=True):
        self.enabled = True
        self.shape = "Rectangle"
        self.cursor = 3 # the 'crosshair'
        self._extent = None
        self.display = display

    def onRectangle(self, rectangle_geometry):
        polygon_extent = utils.extentPolygon(rectangle_geometry)
        layer = utils.selectedLayer()
        if layer is None:
            return None

        output_feature = 'in_memory/compare_selection_points'
        utils.intersectFeatures(layer.name, polygon_extent, output_feature)

        res2 = utils.selectIndividuals(output_feature, False)

        # now, get the results from the summarize encounters tool
        # XXX: ss = SummarizeEncounters()
        # XXX: ss.onRectangle() # doesn't work; won't get the geom
         
        if self.display:
            if config.primary_results is not None:
                res = config.primary_results['indiv_stats']

                common_indiv = res['unique'].intersection(res2['unique']) 
                # compare the two sets of results
                msg = ("First Set:  {0} samples, "
                       "{1} unique individuals\n"
                       "Second Set: {2} samples, "
                       "{3} unique individuals\n\n"
                       "Common to both: {4}".format(
                           len(res['indiv']), len(res['unique']),
                           len(res2['indiv']), len(res2['unique']),
                           len(common_indiv)))
                title = "Comparison Results" 
                pythonaddins.MessageBox(msg, title)
            else:
                pythonaddins.Messagebox("please select first set", "selection missing")

class LayerCombo(object):
    """Implementation for genegis_layer_combo.combobox (Combobox)"""
    def __init__(self):
        self.layers = []
        self.items = ['genetic_points']
        self.editable = True
        self.enabled = True
        self.dropdownWidth = "WWWWWWW"
        self.width = "WWWWWWW"
        self.value = None

    def onSelChange(self, selection):
        if selection:
            config.selected_layer = utils.getLayerByName(selection)
            # FIXME: check how much memory the object will soak up 
            # prior to loading
            config.selected_object = None
        pass

    def onFocus(self, focused):
        # update the layer list _only_ on focus events, preventing this from
        # being triggered on the addin startup.
        if focused:
            self.layers = utils.currentLayers()
            if len(self.layers) > 0:
                self.items = [l.name for l in self.layers]
    def onEnter(self):
        pass
    def refresh(self):
        pass
