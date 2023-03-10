import arcpy
import shutil
import os

from PublicInspectionArcGIS.Utils import ToolboxLogger, Configuration
from PublicInspectionArcGIS.PublicInspection import PublicInspection

class SetupDataSources(PublicInspection) :
    def __init__(self, configuration : Configuration, aprx : arcpy.mp.ArcGISProject):
        super().__init__(configuration, aprx)

        self.loadDataSourcePath = None
        self.SURVEY_DATASET_NAME = configuration.getConfigKey("SURVEY_DATASET_NAME")
        self.INSPECTION_DATASET_NAME = configuration.getConfigKey("INSPECTION_DATASET_NAME")
        self.PARCEL_XML_PATH = configuration.getConfigKey("PARCEL_XML_PATH")
        self.LOAD_XML_PATH = configuration.getConfigKey("LOAD_XML_PATH")
        self.LADM_XML_PATH = configuration.getConfigKey("LADM_XML_PATH")
        self.PARCEL_TYPE = configuration.getConfigKey("PARCEL_TYPE")
        self.PARCEL_RECORD_FIELD = configuration.getConfigKey("PARCEL_RECORD_FIELD")
        self.PARCEL_FABRIC_PATH = configuration.getConfigKey("PARCEL_FABRIC_PATH")
        self.PARCEL_DATASET = configuration.getConfigKey("PARCEL_DATASET")
        self.REFERENCE_OBJECTS_DATASET = configuration.getConfigKey("REFERENCE_OBJECTS_DATASET")
        self.INSPECTION_MAP = configuration.getConfigKey("INSPECTION_MAP")
        self.LAYERFILES_RELATIVE_PATH = configuration.getConfigKey("LAYERFILES_RELATIVE_PATH")

        self.TEMPORAL_ID_PATTERN = "temp_{}_id"
        self.TEMPORAL_NAME_PATTERN = "Temp {} ID"
        self.folder = self.aprx.homeFolder

        self.inspectionDataSource = os.path.join(self.folder, self.INSPECTION_DATASET_NAME)
        self.surveyDataSource = os.path.join(self.folder, self.SURVEY_DATASET_NAME)
        self.layerFilesPath = os.path.join(self.pythonFolder, self.LAYERFILES_RELATIVE_PATH)

        ToolboxLogger.info("Proyect File:           {}".format(aprx.filePath))
        ToolboxLogger.info("Survey Data Source:     {}".format(self.surveyDataSource))
        ToolboxLogger.info("Inspection Data Source: {}".format(self.inspectionDataSource))
        ToolboxLogger.info("xml workspace File:     {}".format(self.PARCEL_XML_PATH))

        if self.da is not None :
            ToolboxLogger.debug("Data Access Object:     {}".format(self.da))
    
    @ToolboxLogger.log_method
    def createSurveyDataSource(self):
        file_folder_path = os.path.dirname(os.path.realpath(__file__))
        xml_path = os.path.join(self.pythonFolder, self.LOAD_XML_PATH)
        arcpy.management.ExportXMLWorkspaceDocument(self.loadDataSourcePath, xml_path)
        ToolboxLogger.info("Load data Exported")

        if(os.path.exists(self.surveyDataSource)) :
            arcpy.Delete_management(self.surveyDataSource)

        arcpy.management.CreateFileGDB(self.folder, self.SURVEY_DATASET_NAME, "CURRENT")
        ToolboxLogger.info("Survey Dataset Created")
        arcpy.management.ImportXMLWorkspaceDocument(self.surveyDataSource, xml_path)
        ToolboxLogger.info("Survey Data Imported")

        arcpy.management.Delete(xml_path)    

    @ToolboxLogger.log_method
    def cleanInspectionMap(self) :
        map = self.aprx.listMaps(self.INSPECTION_MAP)[0]

        layers = [l for l in map.listLayers() if not l.isBasemapLayer]
        for layer in layers :
            map.removeLayer(layer)
        
        tables = map.listTables()
        for table in tables :
            map.removeTable(table)   
        
        bookmarks = map.listBookmarks("Colombia")
        if len(bookmarks) > 0 :
            if self.aprx.activeView is not None :
                self.aprx.activeView.zoomToBookmark(bookmarks[0])

        ToolboxLogger.info("Inspection Map Cleaned")     

    @ToolboxLogger.log_method
    def createInspectionDataSource(self) :
        if(os.path.exists(self.inspectionDataSource)) :
            arcpy.Delete_management(self.inspectionDataSource)

        arcpy.management.CreateFileGDB(self.folder, self.INSPECTION_DATASET_NAME, "CURRENT")
        ToolboxLogger.info("Inspection Dataset Created")

        file_folder_path = os.path.dirname(os.path.realpath(__file__))
        xml_path = os.path.join(file_folder_path, self.PARCEL_XML_PATH)

        arcpy.management.ImportXMLWorkspaceDocument(self.inspectionDataSource, xml_path, "SCHEMA_ONLY")
        ToolboxLogger.info("Inspection Parcel Fabric Schema Imported")
    
    @ToolboxLogger.log_method
    def appendDataset(self, input_ds):
        ToolboxLogger.info("Appending '{}' Data...".format(input_ds))
        input_ds_path = os.path.join(self.loadDataSourcePath, input_ds)
        output_ds_path = os.path.join(self.inspectionDataSource, input_ds)

        ToolboxLogger.debug("Input:  {}".format(input_ds_path))
        ToolboxLogger.debug("Output: {}".format(output_ds_path))

        result_in = arcpy.management.GetCount(input_ds_path)
        result_in_count = int(result_in[0])

        if result_in_count != 0 :
            input_ds_fields = arcpy.ListFields(input_ds_path)
            output_ds_fields = arcpy.ListFields(output_ds_path)

            fix_rs_field_name = self.TEMPORAL_ID_PATTERN.format(input_ds.lower())
            nf = [x for x in output_ds_fields if x.name.lower() == fix_rs_field_name]
            if(len(nf) == 0):
                out_table = arcpy.management.AddField(output_ds_path, fix_rs_field_name, "GUID", field_alias= self.TEMPORAL_NAME_PATTERN.format(input_ds) , field_is_nullable = "NULLABLE")
                arcpy.management.AddIndex(output_ds_path, [fix_rs_field_name], "GUID_{}".format(fix_rs_field_name))
                ToolboxLogger.debug("Temp '{}' field added.".format(fix_rs_field_name))

                output_ds_fields = arcpy.ListFields(output_ds_path)

            fix_rs_field = [f for f in output_ds_fields if f.name == fix_rs_field_name][0]
            fieldMappings = arcpy.FieldMappings()

            for out_field in output_ds_fields:
                if out_field.type != "OID" and out_field.type != "Geometry":
                    if out_field.name == fix_rs_field_name :
                        gid_input_fields = [f for f in input_ds_fields if f.type.lower() == "globalid"]
                        input_field = gid_input_fields[0] if input_ds_fields else None
                        output_field = fix_rs_field
                    else :
                        input_fields = [f for f in input_ds_fields if f.name.lower() == out_field.name.lower()]
                        input_field = input_fields[0] if input_fields else None
                        output_field = out_field
                        
                    if input_field :
                        fm = arcpy.FieldMap()
                        fm.addInputField(input_ds_path, input_field.name)
                        fm.outputField = output_field
                        fieldMappings.addFieldMap(fm)

            output = arcpy.management.Append(input_ds_path, output_ds_path, "NO_TEST", fieldMappings)
            result_out = arcpy.management.GetCount(output)
        else :
            result_out = []
            result_out.append('0')

        ToolboxLogger.debug("Input Count: {} Output Count: {}".format(result_in[0], result_out[0]))
        ToolboxLogger.info("...'{}' Data Appended".format(input_ds))

    @ToolboxLogger.log_method
    def fixDatasetRelationships(self, dataset) :
        dataset_relationship_classes = [x for x in arcpy.Describe(dataset).children if x.datatype == "RelationshipClass" and x.cardinality != "ManyToMany"]
        relationship_classes_fixed = []

        for relationship_class in dataset_relationship_classes:
            origin_classnames = [x for x in relationship_class.originClassNames if not x.lower().__contains__("publicinspection")]
            origin_classname = origin_classnames[0] if origin_classnames else None
            if origin_classname :
                origin_classname_path = os.path.join(dataset, origin_classname)
                origin_classname_fields = arcpy.ListFields(origin_classname_path)
                fix_rs_fields = [f for f in origin_classname_fields if f.name == self.TEMPORAL_ID_PATTERN.format(origin_classname.lower())]
                fix_rs_field = fix_rs_fields[0] if fix_rs_fields else None
                if fix_rs_field :
                    ToolboxLogger.debug("Origin Classname '{}'.".format(origin_classname))
                    destination_classnames = relationship_class.destinationClassNames
                    origin_pk_name =[k[0] for k in relationship_class.originClassKeys if k[1] == "OriginPrimary"][0]
                    origin_fk_name =[k[0] for k in relationship_class.originClassKeys if k[1] == "OriginForeign"][0]
                    origin_registers = self.da.search(origin_classname, [origin_pk_name, fix_rs_field.name])
                    ToolboxLogger.debug("Origin register count = {}.".format(len(origin_registers)))
                    for destination_classname in destination_classnames:
                        ToolboxLogger.debug("Destination Classname '{}'.".format(destination_classname))

                        destination_registers = self.da.search(destination_classname)
                        relationship_classes_fixed.append(relationship_class)
                        ToolboxLogger.debug("Fixing Relationship '{}'.".format(relationship_class.name))

                        ToolboxLogger.debug("Destination register count = {}.".format(len(destination_registers)))
                        if len(destination_registers) > 0:

                            for register in origin_registers:
                                fix_rs_value = register[fix_rs_field.name]

                                self.da.update(destination_classname, [origin_fk_name], [register[origin_pk_name]], "{} = '{}'".format(origin_fk_name, fix_rs_value))
   
    @ToolboxLogger.log_method           
    def cleanFixRelationshipsData(self, dataset) :
        ToolboxLogger.info("Cleaning Fixed Relationships...")
        dataset_relationship_classes = [x for x in arcpy.Describe(dataset).children if x.datatype == "RelationshipClass" and x.cardinality != "ManyToMany"]

        for relationship_class in dataset_relationship_classes:
            ToolboxLogger.debug("Relationship '{}' fixed.".format(relationship_class.name))
            origin_classnames = [x for x in relationship_class.originClassNames if not x.lower().__contains__("publicinspection")]
            origin_classname = origin_classnames[0] if origin_classnames else None
            if origin_classname :
                origin_classname_path = os.path.join(dataset, origin_classname)

                origin_classname_fields = arcpy.ListFields(origin_classname_path)
                fix_rs_fields = [f for f in origin_classname_fields if f.name == self.TEMPORAL_ID_PATTERN.format(origin_classname.lower())]
                fix_rs_field = fix_rs_fields[0] if fix_rs_fields else None
                if fix_rs_field :
                    arcpy.management.DeleteField(origin_classname_path, fix_rs_field.name)
                    ToolboxLogger.debug("Temporal '{}' field deleted.".format(fix_rs_field.name))

            destination_classnames = relationship_class.destinationClassNames
            for destination_classname in destination_classnames :
                destination_classname_path = self.da.findTablePath(destination_classname)
                destination_classname_fields = arcpy.ListFields(destination_classname_path)
                fix_rs_fields = [f for f in destination_classname_fields if f.name == self.TEMPORAL_ID_PATTERN.format(destination_classname.lower())]
                fix_rs_field = fix_rs_fields[0] if fix_rs_fields else None
                if fix_rs_field :
                    null_fix_rs_fields = self.da.search(destination_classname, [fix_rs_field.name], "{} IS NULL".format(fix_rs_field.name))
                    if(len(null_fix_rs_fields) > 0) :
                        self.da.delete(destination_classname, filter = "{} IS NULL".format(fix_rs_field.name))
                    arcpy.management.DeleteField(destination_classname_path, fix_rs_field.name)
                    ToolboxLogger.debug("Temporal '{}' field deleted.".format(fix_rs_field.name))

    @ToolboxLogger.log_method
    def fixRelationships(self):
        ToolboxLogger.info("Fixing relationships...")
        self.fixDatasetRelationships(self.inspectionDataSource)
        self.fixDatasetRelationships(os.path.join(self.inspectionDataSource, "Parcel"))
        self.fixDatasetRelationships(os.path.join(self.inspectionDataSource, "ReferenceObjects"))

        self.cleanFixRelationshipsData(self.inspectionDataSource)
        self.cleanFixRelationshipsData(os.path.join(self.inspectionDataSource, "Parcel"))
        self.cleanFixRelationshipsData(os.path.join(self.inspectionDataSource, "ReferenceObjects"))

    @ToolboxLogger.log_method
    def appendParcelData(self) :
        arcpy.env.workspace = self.loadDataSourcePath

        featureClasses = arcpy.ListFeatureClasses()
        for input_fc in featureClasses:
            self.appendDataset(input_fc)

        tables = arcpy.ListTables()
        for input_tb in tables:
            self.appendDataset(input_tb)

    @ToolboxLogger.log_method
    def createParcelRecords(self) : 
        in_parcel_features = os.path.join(self.inspectionDataSource, self.PARCEL_TYPE)
        arcpy.parcel.CreateParcelRecords(in_parcel_features, self.PARCEL_RECORD_FIELD, "","FIELD") 
        ToolboxLogger.info("Parcel Records Created")

    @ToolboxLogger.log_method
    def buildParcelFabric(self):
        in_parcel_fabric_path = os.path.join(self.inspectionDataSource, self.PARCEL_FABRIC_PATH)
        arcpy.parcel.BuildParcelFabric(in_parcel_fabric_path, "MAXOF")
        ToolboxLogger.info("Parcel Fabric Built")

    @ToolboxLogger.log_method
    def updateInspectionMap(self) :
        map = self.aprx.listMaps(self.INSPECTION_MAP)[0]
        datasets = [self.REFERENCE_OBJECTS_DATASET, self.PARCEL_DATASET]
        for dataset in datasets :
            in_dataset = os.path.join(self.inspectionDataSource, dataset)  
            map.addDataFromPath(in_dataset)

        workspace = arcpy.env.workspace
        arcpy.env.workspace = self.inspectionDataSource
        tables = [table for table in arcpy.ListTables() if not table.lower().__contains__("__attach")]
        for table in tables:
            add_table = arcpy.mp.Table(os.path.join(self.inspectionDataSource, table))
            map.addTable(add_table)
        arcpy.env.workspace = workspace

        full_extent_polygon = None
        layers =  [l for l in map.listLayers() if not l.isBasemapLayer]
        spatialunit_layer = [l for l in layers if l.name.lower() == self.SPATIAL_UNIT_NAME.lower()][0]
        boundary_layer = [l for l in layers if l.name.lower() == self.BOUNDARY_NAME.lower()][0]
        map.moveLayer(spatialunit_layer, boundary_layer, "BEFORE")

        for layer in layers :
            if layer.isFeatureLayer and layer.supports("DEFINITIONQUERY") and arcpy.Exists(layer.dataSource):
                fields = [field for field in arcpy.ListFields(layer.dataSource) if field.name.lower() == "retiredbyrecord"]
                if len(fields) > 0 :
                    layer.definitionQuery = "RetiredByRecord is null"

                    historic_layer = map.addDataFromPath(layer.dataSource)
                    historic_layer.definitionQuery = "RetiredByRecord is not null"
                    historic_layer.visible = False
                    historic_layer.name = "Historic {}".format(layer.name)
                    map.moveLayer(layer, historic_layer, "AFTER")

            layer_file_path = os.path.join(self.layerFilesPath.format(layer.longName))
            exist = os.path.exists(layer_file_path)
            layer.visible = exist

            if layer.supports("DATASOURCE") and arcpy.Exists(layer.dataSource):
                descDS = arcpy.Describe(layer.dataSource)
                if descDS.extent is not None and descDS.extent.height > 0 and descDS.extent.width > 0 :
                    if full_extent_polygon is None :
                        full_extent_polygon = descDS.extent.polygon
                    else :
                        full_extent_polygon = full_extent_polygon.union(descDS.extent.polygon)

            if exist :
                lyrfile = arcpy.mp.LayerFile(layer_file_path)
                lyr = lyrfile.listLayers(layer.name)[0]
                layer.symbology = lyr.symbology

                ToolboxLogger.info("Appling Symbology From Layer: {}.lyrx".format(layer.name))

        extent = self.expand_extent(full_extent_polygon.extent, 1.2)

        if self.aprx.activeMap != map:
            map.openView()

        if self.aprx.activeView :
            view = self.aprx.activeView
            view.camera.setExtent(extent)
            
        try :
            self.aprx.save()

        except Exception as e :
            ToolboxLogger.error(e)

    #Validate load data source
    @ToolboxLogger.log_method
    def validateLoadDataSource(self) :
        validation_errors = []
        if not self.loadDataSourcePath :
            raise Exception("Load Data Source is not set.")

        if not os.path.exists(self.loadDataSourcePath) :
            raise Exception("Load Data Source does not exist.")

        file_folder_path = os.path.dirname(os.path.realpath(__file__))
        xml_path = os.path.join(file_folder_path, self.LADM_XML_PATH)

        VALIDATION_DATASET_NAME = "validation.gdb"
        validationDatasetPath = os.path.join(self.folder, VALIDATION_DATASET_NAME)

        if(os.path.exists(validationDatasetPath)) :
            arcpy.Delete_management(validationDatasetPath)

        arcpy.management.CreateFileGDB(self.folder, VALIDATION_DATASET_NAME, "CURRENT")
        ToolboxLogger.info("Validation Dataset Created")

        arcpy.management.ImportXMLWorkspaceDocument(validationDatasetPath, xml_path, "SCHEMA_ONLY")

        workspace = arcpy.env.workspace
        arcpy.env.workspace = validationDatasetPath

        origin_featureClasses = arcpy.ListFeatureClasses()
        origin_tables = arcpy.ListTables()
        origin_objects = origin_featureClasses + origin_tables

        arcpy.env.workspace = self.loadDataSourcePath
        target_featureClasses = arcpy.ListFeatureClasses()
        target_tables = arcpy.ListTables()
        target_objects = target_featureClasses + target_tables

        arcpy.env.workspace = workspace

        for origin_object in origin_objects :
            if origin_object not in target_objects :
                validation_errors.append("Load Data Source does not contain '{}' feature class.".format(origin_object))
            else :
                origin_fields = arcpy.ListFields(os.path.join(validationDatasetPath, origin_object))
                target_fields = arcpy.ListFields(os.path.join(self.loadDataSourcePath, origin_object))
                for origin_field in origin_fields :
                    if origin_field.name not in [f.name for f in target_fields] :
                        validation_errors.append("Load Data Source does not contain '{}' field in '{}' feature class.".format(origin_field.name, origin_object))
                    else :
                        for target_field in target_fields :
                            if target_field.name == origin_field.name :
                                if target_field.type != origin_field.type :
                                    validation_errors.append("Load Data Source '{}' field in '{}' feature class has different type.".format(origin_field.name, origin_object))
                                if target_field.length != origin_field.length :
                                    validation_errors.append("Load Data Source '{}' field in '{}' feature class has different length.".format(origin_field.name, origin_object))
                                if target_field.isNullable != origin_field.isNullable :
                                    validation_errors.append("Load Data Source '{}' field in '{}' feature class has different nullable.".format(origin_field.name, origin_object))
                                if target_field.domain != origin_field.domain :
                                    validation_errors.append("Load Data Source '{}' field in '{}' feature class has different domain.".format(origin_field.name, origin_object))
                                break

        arcpy.management.Delete(validationDatasetPath)
        ToolboxLogger.info("Validation done")
        return len(validation_errors)==0, validation_errors

    @ToolboxLogger.log_method
    def execute(self) :
        ToolboxLogger.info("Load Data Source:       {}".format(self.loadDataSourcePath))
        try:
            validation, validation_errors = self.validateLoadDataSource()
            if validation :
                self.createSurveyDataSource()
                self.cleanInspectionMap()
                self.createInspectionDataSource()
                self.appendParcelData()
                self.fixRelationships()
                self.createParcelRecords()
                self.buildParcelFabric()
                self.updateInspectionMap()
            else :
                ToolboxLogger.error("Validation Errors: {}".format("\n".join(validation_errors)))

        except Exception as e :
            ToolboxLogger.error(e)
