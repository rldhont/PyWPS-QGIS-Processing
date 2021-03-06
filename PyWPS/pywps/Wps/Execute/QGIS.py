
# first qgis
from qgis.core import *
# next Qt
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from pywps import config
import os
import urllib2
import logging
import tempfile

class QGIS:

    project = None
    projectFileName = None
    outputs = None
    process = None
    sessionId = None

    def __init__(self,process,sessId):
    
        tmp = os.path.basename(tempfile.mkstemp()[1])
        self.outputs = {}
        self.process = process
        self.sessionId = sessId
        
        self.project = QgsProject.instance()
        
        self.projectFileName = os.path.join(config.getConfigValue("server","outputPath"),self.sessionId+".qgs")
        self.project.writePath( self.projectFileName )
        
        self.project.setTitle( "%s-%s"%(self.process.identifier,self.sessionId) )
        self.project.writeEntry("WMSServiceCapabilities", "/", True)
        self.project.writeEntry("WMSServiceTitle", "/", config.getConfigValue("wps","title"))
        self.project.writeEntry("WMSServiceAbstract", "/", config.getConfigValue("wps","abstract"))
        self.project.writeEntry("WMSKeywordList", "/", config.getConfigValue("wps","keywords"))
        self.project.writeEntry("WMSFees", "/", config.getConfigValue("wps","fees"))
        self.project.writeEntry("WMSAccessConstraints", "/", config.getConfigValue("wps","constraints"))
        self.project.writeEntry("WMSContactOrganization", "/", config.getConfigValue("provider","providerName"))
        self.project.writeEntry("WMSContactPerson", "/", config.getConfigValue("provider","individualName"))
        self.project.writeEntry("WMSContactPhone", "/", config.getConfigValue("provider","phoneVoice"))
        self.project.writeEntry("WMSContactPhone", "/", config.getConfigValue("provider","electronicMailAddress"))
        
        self.project.write( QFileInfo( self.projectFileName ) )
        
    def getReference(self,output):
        
        mlr = QgsMapLayerRegistry.instance()
        logging.info(output.identifier+' '+output.value)
        layersByName = mlr.mapLayersByName( output.identifier )
        outputLayer = None
        if not layersByName :
            if output.format["mimetype"] == 'image/tiff' :
                outputLayer = QgsRasterLayer( output.value, output.identifier, 'gdal' )
                mlr.addMapLayer( outputLayer )
            else :
                outputLayer = QgsVectorLayer( output.value, output.identifier, 'ogr' )
                mlr.addMapLayer( outputLayer )
        else :
            outputLayer = layersByName[0]
        treeRoot = self.project.layerTreeRoot()
        if not treeRoot.findLayer( outputLayer.id() ) :
            treeRoot.addLayer( outputLayer )
            
        self.project.write( QFileInfo( self.projectFileName ) )
        
        if outputLayer.type() == QgsMapLayer.VectorLayer :
            WFSLayers = self.project.readListEntry( "WFSLayers", "/" )[0]
            if outputLayer.id() not in WFSLayers :
                WFSLayers.append( outputLayer.id() )
                self.project.writeEntry( "WFSLayers", "/", WFSLayers )
                self.project.write( QFileInfo( self.projectFileName ) )
            return self.getMapServerWFS(output)
                
        elif outputLayer.type() == QgsMapLayer.RasterLayer :
            output.projection = outputLayer.crs().authid()
            output.height = outputLayer.height()
            output.width = outputLayer.width()
            outputExtent = outputLayer.extent()
            output.bbox = [outputExtent.xMinimum(), outputExtent.yMinimum(), outputExtent.xMaximum(), outputExtent.yMaximum()]
            WCSLayers = self.project.readListEntry( "WCSLayers", "/" )[0]
            if outputLayer.id() not in WCSLayers :
                WCSLayers.append( outputLayer.id() )
                self.project.writeEntry( "WCSLayers", "/", WCSLayers )
                self.project.write( QFileInfo( self.projectFileName ) )
            return self.getMapServerWCS(output)
        
    def getMapServerWCS(self,output):
        """Get the URL for mapserver WCS request of the output"""
        return config.getConfigValue("qgis","qgisserveraddress")+ "?map="+self.projectFileName+ "&SERVICE=WCS"+ "&REQUEST=GetCoverage"+ "&VERSION=1.0.0"+ "&COVERAGE="+output.identifier+"&CRS="+output.projection.replace("+init=","")+ ("&BBOX=%s,%s,%s,%s"%(output.bbox[0],output.bbox[1],output.bbox[2],output.bbox[3]))+ "&HEIGHT=%s" %(output.height)+("&WIDTH=%s"%(output.width))+("&FORMAT=%s"%output.format["mimetype"])

    def getMapServerWFS(self,output):
        """Get the URL for mapserver WFS request of the output"""
        return config.getConfigValue("qgis","qgisserveraddress")+"?map="+self.projectFileName+"&SERVICE=WFS"+ "&REQUEST=GetFeature"+ "&VERSION=1.0.0"+"&TYPENAME="+output.identifier
