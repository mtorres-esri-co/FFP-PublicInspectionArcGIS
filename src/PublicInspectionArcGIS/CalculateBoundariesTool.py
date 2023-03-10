import arcpy

from PublicInspectionArcGIS.Utils import ARCGIS_HANDLER, STREAM_HANDLER, ToolboxLogger
from PublicInspectionArcGIS.ToolsLib import PublicInspectionTools

class CalculateBoundariesTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate All Boundaries"
        self.description = "Calculate Boundaries All Spatial Units for Public Inspection"
        self.alias = "CalculateBoundariesTool"
        
        self.canRunInBackground = True

        if ToolboxLogger._logger is None:
            ToolboxLogger.initLogger(handler_type = STREAM_HANDLER | ARCGIS_HANDLER )
            ToolboxLogger.setInfoLevel()

        try :         
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            self.tool = PublicInspectionTools.getCalculateBoundaries(aprx)
        except Exception as e:  
            self.tool = None
            ToolboxLogger.debug("Error initializing CalculateBoundariesTool: {}".format(e))

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = []
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        if self.tool is not None:
            self.tool.execute()

        return
