import arcpy

from PublicInspectionArcGIS.Utils import ARCGIS_HANDLER, STREAM_HANDLER, ToolboxLogger
from PublicInspectionArcGIS.ToolsLib import PublicInspectionTools

class GenerateCertificateTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Generate Certificate"
        self.description = ""
        self.alias = "GenerateCertificateTool"
        
        self.Params = {"legal_id": 0,"visitor_contact": 1}
        self.canRunInBackground = True

        if ToolboxLogger._logger is None:
            ToolboxLogger.initLogger(handler_type = STREAM_HANDLER | ARCGIS_HANDLER )
            ToolboxLogger.setInfoLevel()
        try :         
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            self.tool = PublicInspectionTools.getCalculateCertificate(aprx=aprx)
        except Exception as e:  
            self.tool = None
            ToolboxLogger.debug("Error initializing GenerateCertificateTool: {}".format(e))

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = []

        param = arcpy.Parameter(
            displayName="Legal ID",
            name="legal_id",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        params.insert(self.Params["legal_id"], param)
        
        param = arcpy.Parameter(
            displayName="visitor contact",
            name="visitor_contact",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        params.insert(self.Params["visitor_contact"], param)
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        if not parameters[self.Params["legal_id"]].altered :
            selected_spatialunits = self.tool.get_selected_spatialunits()
            legal_ids = [spatialunit["legal_id"] for spatialunit in selected_spatialunits]

            if len(legal_ids) > 0:
                parameters[self.Params["legal_id"]].filter.list = legal_ids
                parameters[self.Params["legal_id"]].value = None
            else :
                parameters[self.Params["legal_id"]].filter.list = None
                parameters[self.Params["legal_id"]].value = None

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return
    
    def execute(self,parameters, messages):
        """The source code of the tool."""
        legal_id = parameters[self.Params["legal_id"]].valueAsText
        visitor_contact = parameters[self.Params["visitor_contact"]].valueAsText
        
        self.tool.legal_id=legal_id
        self.tool.visitor_contact=visitor_contact
        self.tool.execute() 
        
        return    