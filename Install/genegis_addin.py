import os
import sys
import webbrowser
from threading import Thread

import arcpy
import pythonaddins

# enable local imports
local_path = os.path.dirname(__file__)
for path in [local_path, os.path.join(local_path, 'toolbox')]:
    sys.path.insert(0, os.path.abspath(path))

# import local settings
import config
import utils

# get the paths for our toolboxes
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

class ExportAIS(object):
    """Implementation for genegis_export_ais.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        utils.toolDialog(genegis_toolbox, "ExportAllelesInSpace")

class ExportGenAlEx(object):
    """Implementation for genegis_export_genalex.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        utils.toolDialog(genegis_toolbox, "ExportGenAlEx")

class ExportGenepop(object):
    """Implementation for genegis_export_genepop.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        utils.toolDialog(genegis_toolbox, "ExportGenepop")

class ExportKML(object):
    """Implementation for genegis_export_kml.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        # TODO: update this to custom code (issue #22)
        utils.toolDialog("Conversion Tools", "LayerToKML")

class ExportSRGD(object):
    """Implementation for genegis_export_srgd.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False

    def onClick(self):
        #with open("c:\\log\\genegis-export-srgd.csv", 'w') as f:
        #    f.write("onclick Called! trying to get layer combo value...\n")
        fc = config.selected_layer
        if fc is None:
            msg = "Nothing selected. Please enter a valid layer into the geneGIS selection box."
            title = "Export SRGD: ComboBox value"
            #f.write("writing message box...\n")
            pythonaddins.MessageBox(msg, title)
        else: 
            #f.write("have a valid layer selected, %s\n" % fc)
            output_path = pythonaddins.SaveDialog("Output SRGD file name", "SRGD_%s.csv" % fc)
            #f.write("got output_path = `%s`\n" % output_path)
            utils.writeToSRGD(fc, output_path)

# genetic analysis tools
#
class calculateFst(object):
    """Implementation for genegis_calculate_fst.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        utils.toolDialog(genegis_toolbox, "SpagediFst")

# geographic analysis tools
#
class computeDistanceMatrix(object):
    """Implementation for genegis_calculate_fst.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        utils.toolDialog(genegis_toolbox, "DistanceMatrix")

class computeDistancePaths(object):
    """Implementation for genegis_calculate_fst.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        utils.toolDialog(genegis_toolbox, "ShortestDistancePaths")

class individualPaths(object):
    """Implementation for genegis_calculate_fst.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        utils.toolDialog(genegis_toolbox, "MakeIndividualPaths")
# help
#

def OpenBrowserURL(target_url):
    webbrowser.open(target_url,new=2)

class helpWebsiteHome(object):
    """Implementation for genegis_website_home.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        target_url = "http://genegis.org"
        t = Thread(target=OpenBrowserURL, args=[target_url])
        t.start()
        t.join()

class helpWebsiteDocs(object):
    """Implementation for genegis_website_home.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        target_url = "http://genegis.org/documentation.html"
        t = Thread(target=OpenBrowserURL, args=[target_url])
        t.start()
        t.join()


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

        # XXX now, get the results from the summarize encounters tool,
        # and add these selection results back to the table
        """
        fields = arcpy.ListFields(layer.dataSource)

        try:
            field_name = 'Selected_Populations'
            if field_name not in fields:
                with open(config.log_path, 'a') as f:
                    f.write("trying to add %s to %s\n" % (field_name, layer.dataSource))
               
                arcpy.AddField_management(layer.dataSource, field_name, 'SHORT')
            #utils.msg("Added a formatted date field: {field_name}.".format(field_name=field_name))
            with open(config.log_path, 'a') as f:
                f.write("trying to add %s to %s\n" % (field_name, layer.dataSource))
           
            if config.primary_results is None:
                pythonaddins.MessageBox("please make first selection before running this tool", "requires primary selection")
                return None

            first_pop = config.primary_results['indiv_stats']['unique']
            second_pop = res2['unique']
            #pythonaddins.MessageBox("got %i in pop1, %i in pop2" % (len(first_pop), len(second_pop)), "pop compare")
            with arcpy.da.UpdateCursor(layer, [config.settings.id_field, field_name]) as cur:
                for row in cur:
                    indiv = row[0]
                    if indiv in first_pop and indiv in second_pop:
                        pop = 3
                    elif indiv in second_pop:
                        pop = 2
                    elif indiv in first_pop:
                        pop = 1
                    else:
                        pop = None
                    row[1] = pop
                    cur.updateRow(row)
                        
        except Exception as e:
            msg = "Error adding Selected_Populations column."
            title = "Compare Encounters: Selecting Populations"
            with open(config.log_path, 'a') as f:
                f.write("generated Exception: %s\n" % e)

            pythonaddins.MessageBox(msg, title)
            return None
        """
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
        self.dropdownWidth = "WWWWWWWWWWWWWWWWWWWW"
        self.width = "WWWWWWWWWWWWWWWWWWWW"
        self.value = utils.loadDefaultLayer()

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

class geneGISExtension(object):
    """Implementation for genegis_layer_combo.combobox (Combobox)"""
    def __init__(self):
        self.enabled = True

    def itemAdded(self, new_item):
        lc = LayerCombo()
        val = utils.loadDefaultLayer()
        lc.value = val
        lc.refresh()
