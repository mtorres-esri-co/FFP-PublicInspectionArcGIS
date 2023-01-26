# -*- coding: utf-8 -*-
from PublicInspectionArcGIS.Utils import ToolboxLogger, STREAM_HANDLER, ARCGIS_HANDLER
from PublicInspectionArcGIS.SetupDataSourcesTool import SetupDataSourcesTool
from PublicInspectionArcGIS.CalculateBoundariesTool import CalculateBoundariesTool
from PublicInspectionArcGIS.CalculateSpatialUnitBoundariesTool import CalculateSpatialUnitBoundariesTool
from PublicInspectionArcGIS.CaptureSignatureTool import CaptureSignatureTool
from PublicInspectionArcGIS.GenerateCertificateTool import GenerateCertificateTool

class Toolbox(object):
    
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "FFP ArcGIS Public Inspection Tools"
        self.alias = "PublicInspectionArcGIS"
        
        # List of tool classes associated with this toolbox
        self.tools = [
            SetupDataSourcesTool, 
            CalculateBoundariesTool, 
            CalculateSpatialUnitBoundariesTool, 
            CaptureSignatureTool, 
            GenerateCertificateTool
        ]

        ToolboxLogger.initLogger(handler_type = STREAM_HANDLER | ARCGIS_HANDLER )
        ToolboxLogger.setInfoLevel()