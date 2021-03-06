# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QuickOSM
                                 A QGIS plugin
 OSM's Overpass API frontend
                             -------------------
        begin                : 2014-06-11
        copyright            : (C) 2014 by 3Liz
        email                : info at 3liz dot com
        contributor          : Etienne Trimaille
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from QuickOSM import *

from QuickOSM.CoreQuickOSM.QueryFactory import QueryFactory
from QuickOSM.CoreQuickOSM.Tools import Tools
from QuickOSM.CoreQuickOSM.API.ConnexionOAPI import ConnexionOAPI
from QuickOSM.CoreQuickOSM.Parser.OsmParser import OsmParser
from processing.tools.system import *
import processing
import ntpath
from os.path import dirname,abspath,join
from genericpath import isfile

class Process:
    '''
    This class makes the link between GUI and Core
    '''
    
    @staticmethod
    def ProcessQuery(dialog = None, query=None, nominatim=None, bbox=None, outputDir=None, prefixFile=None,outputGeomTypes=None, layerName = "OsmQuery", whiteListValues = None, configOutputs = None):
        
        #Prepare outputs
        dialog.setProgressText(QApplication.translate("QuickOSM",u"Prepare outputs"))
        #If a file already exist, we avoid downloading data for nothing
        outputs = {}
        for layer in ['points','lines','multilinestrings','multipolygons']:
            QApplication.processEvents()
            if not outputDir:
                #if no directory, get a temporary shapefile
                outputs[layer] = getTempFilenameInTempFolder("_"+layer+"_quickosm.shp")
            else:
                if not prefixFile:
                    prefixFile = layerName
                    
                outputs[layer] = os.path.join(outputDir,prefixFile + "_" + layer + ".shp")
                
                if os.path.isfile(outputs[layer]):
                    raise FileOutPutException(suffix="("+outputs[layer]+")")
        
        #Replace Nominatim or BBOX
        query = Tools.PrepareQueryOqlXml(query=query, nominatimName = nominatim, extent=bbox)
        
        #Getting the default OAPI and running the query
        server = Tools.getSetting('defaultOAPI')
        dialog.setProgressText(QApplication.translate("QuickOSM",u"Downloading data from Overpass"))
        QApplication.processEvents()
        connexionOAPI = ConnexionOAPI(url=server,output = "xml")
        osmFile = connexionOAPI.getFileFromQuery(query)
        
        #Parsing the file
        osmParser = OsmParser(osmFile, layers=outputGeomTypes, whiteListColumn=whiteListValues)
        osmParser.signalText.connect(dialog.setProgressText)
        osmParser.signalPercentage.connect(dialog.setProgressPercentage)
        layers = osmParser.parse()
        
        #Geojson to shapefile
        numLayers = 0
        dialog.setProgressText(QApplication.translate("QuickOSM",u"From GeoJSON to Shapefile"))
        for i, (layer,item) in enumerate(layers.iteritems()):
            dialog.setProgressPercentage(i/len(layers)*100)  
            QApplication.processEvents()
            if item['featureCount'] and layer in outputGeomTypes:
                
                finalLayerName = layerName
                #If configOutputs is not None (from My Queries)
                if configOutputs:
                    if configOutputs[layer]['namelayer']:
                        finalLayerName = configOutputs[layer]['namelayer']
                
                
                #Transforming the vector file
                osmGeom = {'points':QGis.WKBPoint,'lines':QGis.WKBLineString,'multilinestrings':QGis.WKBMultiLineString,'multipolygons':QGis.WKBMultiPolygon}
                geojsonlayer = QgsVectorLayer(item['geojsonFile'],"temp","ogr")
                writer = QgsVectorFileWriter(outputs[layer], "UTF-8", geojsonlayer.pendingFields(), osmGeom[layer], geojsonlayer.crs(), "ESRI Shapefile")
                for f in geojsonlayer.getFeatures():
                    writer.addFeature(f)
                del writer
                
                #Loading the final vector file
                newlayer = QgsVectorLayer(outputs[layer],finalLayerName,"ogr")
                
                #Try to set styling if defined
                if configOutputs and configOutputs[layer]['style']:
                    newlayer.loadNamedStyle(configOutputs[layer]['style'])
                else:
                    #Loading default styles
                    if layer == "multilinestrings" or layer == "lines":
                        if "colour" in item['tags']:
                            newlayer.loadNamedStyle(join(dirname(dirname(abspath(__file__))),"styles",layer+"_colour.qml"))
                
                #Add action about OpenStreetMap
                actions = newlayer.actions()
                actions.addAction(QgsAction.OpenUrl,"OpenStreetMap Browser",'http://www.openstreetmap.org/browse/[% "osm_type" %]/[% "osm_id" %]',False)
                actions.addAction(QgsAction.GenericPython,'JOSM','from QuickOSM.CoreQuickOSM.Actions import Actions;Actions.run("josm","[% "full_id" %]")',False)
                actions.addAction(QgsAction.OpenUrl,"User default editor",'http://www.openstreetmap.org/edit?[% "osm_type" %]=[% "osm_id" %]',False)
                #actions.addAction(QgsAction.GenericPython,"Edit directly",'from QuickOSM.CoreQuickOSM.Actions import Actions;Actions.run("rawedit","[% "osm_type" %]/[% "osm_id" %]")',False)
                
                for link in ['url','website','wikipedia','ref:UAI']:
                    if link in item['tags']:
                        link = link.replace(":","_")
                        actions.addAction(QgsAction.GenericPython,link,'from QuickOSM.CoreQuickOSM.Actions import Actions;Actions.run("'+link+'","[% "'+link+'" %]")',False)
                
                if 'network' in item['tags'] and 'ref' in item['tags']:
                    actions.addAction(QgsAction.GenericPython,"Sketchline",'from QuickOSM.CoreQuickOSM.Actions import Actions;Actions.runSketchLine("[% "network" %]","[% "ref" %]")',False)
                 
                #Add index
                newlayer.dataProvider().createSpatialIndex()
                                
                QgsMapLayerRegistry.instance().addMapLayer(newlayer)
                numLayers += 1
                
        return numLayers
    
    @staticmethod
    def ProcessQuickQuery(dialog = None, key = None,value = None,bbox = None,nominatim = None,osmObjects = None, timeout=25, outputDir=None, prefixFile=None, outputGeomTypes=None):
        
        #Set the layername
        layerName = ''
        for i in [key,value,nominatim]:
            if i:
                layerName += i + "_"
        #Delete last "_"
        layerName = layerName[:-1]
        
        #Building the query
        queryFactory = QueryFactory(timeout=timeout,key=key,value=value,bbox=bbox,nominatim=nominatim,osmObjects=osmObjects)
        query = queryFactory.make()
        
        #Call ProcessQuery with the new query
        return Process.ProcessQuery(dialog=dialog,
                                    query=query,
                                    nominatim=nominatim,
                                    bbox=bbox,
                                    outputDir=outputDir,
                                    prefixFile=prefixFile,
                                    outputGeomTypes=outputGeomTypes,
                                    layerName=layerName)