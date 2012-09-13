import arcpy
import pythonaddins

def _currentLayer():
    layer = None
    """
    # get the current map document instance
    mxd = arcpy.mapping.MapDocument('current')
    # select our first layer
    layers = arcpy.mapping.ListLayers(mxd, "*")
    """
    layer = pythonaddins.GetSelectedTOCLayerOrDataFrame()
    if layer is None:
        msg = "No point layer selected! please add a point layer."
        title = "No available layer"
        pythonaddins.MessageBox(msg, title)
    # FIXME: check that it contains points (that's all we know how to work 
    # with for the time-being.)

    # FIXME: do something more sophisticated to select the correct layer.
    # something like this should work, provided we know the name of the 
    # input layer.
    """
    for lyr in arcpy.mapping.ListLayers(mxd, "", df):
        if lyr.name == "Tim":
            # Do some stuff.
    """
    return layer

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

class ToolClass2(object):
    """Implementation for genegis_addin.tool (Tool)"""

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
        # the selected layer
        layer = _currentLayer()
        if layer is None:
            return None    

       # extract the coordinates from our extent object
        coords = [[extent.XMin,extent.YMin],[extent.XMax,extent.YMin], \
                [extent.XMax,extent.YMax],[extent.XMin,extent.YMax]]
        # convert it to a polygon, we need this to compute the intersection

        polygon_extent = arcpy.Polygon(arcpy.Array(
            [arcpy.Point(x,y) for x,y in coords]), arcpy.SpatialReference(4326))

        print type(polygon_extent)
        # create an extent object from our selection
        #output_feature = 'in_memory\selection_a_poly'

        # XXX get the selected layer's spatial reference:
        # arcpy.SpatialReference(...) OR point at a prj file.

        #if arcpy.Exists(output_feature):
            
        # now, grab the current _selected_ layer in ArcMap

        # XXX here either use 'Spatial Join' or 'Select Features by Location'
        #arcpy.SpatialJoin_analysis(

class ToolClass4(object):
    """Implementation for genegis_addin.tool_1 (Tool)"""
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
