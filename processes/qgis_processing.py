# -*- coding: utf-8 -*-
"""
***************************************************************************
qgis_processing.py
---------------------
Date : January 2015
Copyright : (C) 2015 by René-Luc D'hont
Email : rldhont at 3liz dot com
***************************************************************************
* *
* This program is free software; you can redistribute it and/or modify *
* it under the terms of the GNU General Public License as published by *
* the Free Software Foundation; either version 2 of the License, or *
* (at your option) any later version. *
* *
***************************************************************************
"""

import types

import sys, os
import inspect

import logging

# first qgis
from qgis.core import *
# next Qt
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from pywps import config
from pywps.Process import WPSProcess
from xml.dom import minidom
from xml.sax.saxutils import escape

from processing.core.Processing import Processing
from processing.core.ProcessingConfig import ProcessingConfig, Setting
from processing.core.parameters import *
from processing.tools.general import *

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)
Processing.initialize()

# load QGIS Processing config
for opt in config.config.options( 'qgis_processing' ):
    opt_val = config.getConfigValue( 'qgis_processing', opt )
    ProcessingConfig.setSettingValue( opt.upper(), opt_val )

# Relaod algorithms
Processing.loadAlgorithms()


def QGISProcessFactory(alg_name):
    """This is the bridge between QGIS Processing and PyWPS:
    it creates PyWPS processes based on QGIS Processing alg name
    it is inspired by Alessandro Pasotti work
    """
    from pywps.Process import WPSProcess
    from new import classobj
    import types
    from processing.core.Processing import Processing
    # Sanitize name
    class_name = alg_name.replace(':', '_')
    alg = Processing.getAlgorithm(alg_name)
    
    # Get project
    projectsFolder = config.getConfigValue( 'qgis', 'projects_folder' )
    projectPath = None
    if os.path.exists(projectsFolder) and os.path.exists( os.path.join( projectsFolder, class_name+'.qgs' ) ) :
        projectPath = os.path.join( projectsFolder, class_name+'.qgs' )
    
    rasterLayers = []
    vectorLayers = []
    if projectPath and os.path.exists( projectPath ) :
        p_dom = minidom.parse( projectPath )
        for ml in p_dom.getElementsByTagName('maplayer') :
            l= {'type':ml.attributes["type"].value,
                'name':ml.getElementsByTagName('layername')[0].childNodes[0].data,
                'datasource':ml.getElementsByTagName('datasource')[0].childNodes[0].data,
                'provider':ml.getElementsByTagName('provider')[0].childNodes[0].data,
                'crs':ml.getElementsByTagName('srs')[0].getElementsByTagName('authid')[0].childNodes[0].data,
                'proj4':ml.getElementsByTagName('srs')[0].getElementsByTagName('proj4')[0].childNodes[0].data
            }
            # Update relative path
            if l['provider'] in ['ogr','gdal'] and str(l['datasource']).startswith('.'):
                l['datasource'] = os.path.abspath( os.path.join( projectsFolder, l['datasource'] ) )
                if not os.path.exists( l['datasource'] ) :
                    continue
            elif l['provider'] in ['gdal'] and str(l['datasource']).startswith('NETCDF:'):
                theURIParts = l['datasource'].split( ":" );
                src = theURIParts[1]
                src.replace( "\"", "" );
                if src.startswith('.') :
                    src = os.path.abspath( os.path.join( projectsFolder, src ) )
                theURIParts[1] = "\"" + src + "\""
                l['datasource'] = ':'.join( theURIParts )
                
            if l['type'] == "raster" :
                rasterLayers.append( l )
            elif l['type'] == "vector" :
                l['geometry'] = ml.attributes["geometry"].value
                vectorLayers.append( l )

    def process_init(self):
        # Automatically init the process attributes
        # Start with help for description
        #isText, help = self.alg.help()
        #logging.info( help )
        #if not isText and help is not None:
        #   with open(help, 'r') as helpFile :
        #      help = helpFile.read()
        # because of a print in ModelerAlgorithm
        # get help can't be used
        # and because of some changes in help method too
        help = None
        # Init WPS Process
        WPSProcess.__init__(self,
            identifier=alg_name, # must be same, as filename
            title=escape(alg.name),
            version = "0.1",
            storeSupported = "true",
            statusSupported = "true",
            abstract= '<![CDATA[' + (help is None and str(alg) or str(help)) + ']]>',
            grassLocation=False)

        # Test parameters
        if not len( self.alg.parameters ):
            self.alg.defineCharacteristics()

        # Add I/O
        i = 1
        for parm in alg.parameters:
            minOccurs = 1
            if getattr(parm, 'optional', False):
                minOccurs = 0
                
            # TODO: create "LiteralValue", "ComplexValue" or "BoundingBoxValue"
            # this can be done checking the class:
            # parm.__class__, one of
            # ['Parameter', 'ParameterBoolean', 'ParameterCrs', 'ParameterDataObject', 'ParameterExtent', 'ParameterFile', 'ParameterFixedTable', 'ParameterMultipleInput', 'ParameterNumber', 'ParameterRange', 'ParameterRaster', 'ParameterSelection', 'ParameterString', 'ParameterTable','ParameterTableField', 'ParameterVector']
            if parm.__class__.__name__ == 'ParameterVector':
                values = []
                if vectorLayers and ParameterVector.VECTOR_TYPE_ANY in parm.shapetype :
                    values = [l['name'] for l in vectorLayers]
                elif vectorLayers :
                    if ParameterVector.VECTOR_TYPE_POINT in parm.shapetype :
                        values += [l['name'] for l in vectorLayers if l['geometry'] == 'Point']
                    if ParameterVector.VECTOR_TYPE_LINE in parm.shapetype :
                        values += [l['name'] for l in vectorLayers if l['geometry'] == 'Line']
                    if ParameterVector.VECTOR_TYPE_POLYGON in parm.shapetype :
                        values += [l['name'] for l in vectorLayers if l['geometry'] == 'Polygon']
                if values :
                    self._inputs['Input%s' % i] = self.addLiteralInput(escape(parm.name), '<![CDATA[' + parm.description + ']]>',
                                                    minOccurs=minOccurs,
                                                    type=types.StringType)
                    self._inputs['Input%s' % i].values = values
                else :
                    self._inputs['Input%s' % i] = self.addComplexInput(escape(parm.name), '<![CDATA[' + parm.description + ']]>',
                        minOccurs=minOccurs, formats = [{'mimeType':'text/xml'}])
                        
            elif parm.__class__.__name__ == 'ParameterRaster':
                if rasterLayers :
                    self._inputs['Input%s' % i] = self.addLiteralInput(escape(parm.name), '<![CDATA[' + parm.description + ']]>',
                                                    minOccurs=minOccurs,
                                                    type=types.StringType)
                    self._inputs['Input%s' % i].values = [l['name'] for l in rasterLayers]
                else :
                    self._inputs['Input%s' % i] = self.addComplexInput(escape(parm.name), '<![CDATA[' + parm.description + ']]>',
                        minOccurs=minOccurs, formats = [{'mimeType':'image/tiff'}])
                        
            elif parm.__class__.__name__ == 'ParameterTable':
                self._inputs['Input%s' % i] = self.addComplexInput(escape(parm.name), '<![CDATA[' + parm.description + ']]>',
                    minOccurs=minOccurs, formats = [{'mimeType':'text/csv'}])
                    
            elif parm.__class__.__name__ == 'ParameterExtent':
                self._inputs['Input%s' % i] = self.addBBoxInput(escape(parm.name), '<![CDATA[' + parm.description + ']]>',
                    minOccurs=minOccurs)
                    
            elif parm.__class__.__name__ == 'ParameterSelection':
                self._inputs['Input%s' % i] = self.addLiteralInput(escape(parm.name), '<![CDATA[' + parm.description + ']]>',
                                                minOccurs=minOccurs,
                                                type=types.StringType,
                                                default=getattr(parm, 'default', None))
                self._inputs['Input%s' % i].values = parm.options
                
            elif parm.__class__.__name__ == 'ParameterRange':
                tokens = self.value.split(',')
                n1 = float(tokens[0])
                n2 = float(tokens[1])
                self._inputs['Input%s' % i] = self.addLiteralInput(escape(parm.name), '<![CDATA[' + parm.description + ']]>',
                                                minOccurs=minOccurs,
                                                type=types.FloatType,
                                                default=n1)
                self._inputs['Input%s' % i].values = ((n1,n2))
                
            else:
                type = types.StringType
                if parm.__class__.__name__ == 'ParameterBoolean':
                    type = types.BooleanType
                elif  parm.__class__.__name__ =='ParameterNumber':
                    type = types.FloatType
                self._inputs['Input%s' % i] = self.addLiteralInput(escape(parm.name), '<![CDATA[' + parm.description + ']]>',
                                                minOccurs=minOccurs,
                                                type=type,
                                                default=getattr(parm, 'default', None))
                if parm.__class__.__name__ == 'ParameterBoolean':
                    self._inputs['Input%s' % i].values=(True,False)
            i += 1
        i = 1
        for parm in alg.outputs:
            # TODO: create "LiteralOutput", "ComplexOutput" or "BoundingBoxOutput"
            # this can be done checking the class:
            # parm.__class__, one of
            # ['Output', 'OutputDirectory', 'OutputExtent', 'OutputFile', 'OutputHtml', 'OutputNumber', 'OutputRaster', 'OutputString', 'OutputTable', 'OutputVector']
            if parm.__class__.__name__ == 'OutputVector':
                self._outputs['Output%s' % i] = self.addComplexOutput(parm.name, parm.description,
                    formats = [{'mimeType':'text/xml'}])
            elif parm.__class__.__name__ == 'OutputRaster':
                self._outputs['Output%s' % i] = self.addComplexOutput(parm.name, parm.description,
                    formats = [{'mimeType':'image/tiff'}])
            elif parm.__class__.__name__ == 'OutputTable':
                self._outputs['Output%s' % i] = self.addComplexOutput(parm.name, parm.description,
                    formats = [{'mimeType':'text/csv'}])
            elif parm.__class__.__name__ == 'OutputHtml':
                self._outputs['Output%s' % i] = self.addComplexOutput(parm.name, parm.description,
                    formats = [{'mimeType':'text/html'}])
            elif parm.__class__.__name__ == 'OutputExtent':
                self._outputs['Output%s' % i] = self.addBBoxOutput(parm.name, parm.description,
                    minOccurs=minOccurs)
            else:
                type = types.StringType
                if  parm.__class__.__name__ =='OutputNumber':
                    type = types.FloatType
                self._outputs['Output%s' % i] = self.addLiteralOutput(parm.name, parm.description,
                                                type=type)
            i += 1

        for k in self._inputs:
             setattr(self, k, self._inputs[k])

        for k in self._outputs:
             setattr(self, k, self._outputs[k])



    def execute(self):
        # create a project
        p = QgsProject.instance()
        mlr = QgsMapLayerRegistry.instance()
        # Run alg with params
        # TODO: get args
        args = {}
        for k in self._inputs:
            v = getattr(self, k)
            parm = self.alg.getParameterFromName( v.identifier )
            if parm.__class__.__name__ == 'ParameterVector':
                values = []
                if vectorLayers and ParameterVector.VECTOR_TYPE_ANY in parm.shapetype :
                    values = [l['name'] for l in vectorLayers]
                elif vectorLayers :
                    if ParameterVector.VECTOR_TYPE_POINT in parm.shapetype :
                        values += [l['name'] for l in vectorLayers if l['geometry'] == 'Point']
                    if ParameterVector.VECTOR_TYPE_LINE in parm.shapetype :
                        values += [l['name'] for l in vectorLayers if l['geometry'] == 'Line']
                    if ParameterVector.VECTOR_TYPE_POLYGON in parm.shapetype :
                        values += [l['name'] for l in vectorLayers if l['geometry'] == 'Polygon']
                if values :
                    layerName = v.getValue() 
                    values = [l for l in values if l['name'] == layerName]
                    l = values[0]
                    layer = QgsVectorLayer( l['datasource'], l['name'], l['provider'] )
                    mlr.addMapLayer( layer, False )
                    args[v.identifier] = layer
                else :
                    fileName = v.getValue()
                    fileInfo = QFileInfo( fileName )
                    # move fileName to fileName.gml for ogr
                    with open( fileName, 'r' ) as f :
                        o = open( fileName+'.gml', 'w' )
                        o.write( f.read() )
                        o.close()
                    import shutil
                    shutil.copy2(fileName+'.gml', '/tmp/test.gml' )
                    # get layer
                    layer = QgsVectorLayer( fileName+'.gml', fileInfo.baseName(), 'ogr' )
                    pr = layer.dataProvider()
                    e = layer.extent()
                    mlr.addMapLayer( layer, False )
                    args[v.identifier] = layer
                    
            elif parm.__class__.__name__ == 'ParameterRaster':
                if rasterLayers :
                    layerName = v.getValue() 
                    values = [l for l in rasterLayers if l['name'] == layerName]
                    l = values[0]
                    layer = QgsRasterLayer( l['datasource'], l['name'], l['provider'] )
                    crs = l['crs']
                    qgsCrs = None
                    if str(crs).startswith('USER:') :
                        qgsCrs = crs = QgsCoordinateReferenceSystem()
                        qgsCrs.createFromProj4( str(l['proj4']) )
                    else :
                        qgsCrs = QgsCoordinateReferenceSystem(crs, QgsCoordinateReferenceSystem.EpsgCrsId)
                    if qgsCrs :
                        layer.setCrs( qgsCrs )
                    mlr.addMapLayer( layer, False )
                    args[v.identifier] = layer
                else :
                    fileName = v.getValue()
                    fileInfo = QFileInfo( fileName )
                    layer = QgsRasterLayer( fileName, fileInfo.baseName(), 'gdal' )
                    mlr.addMapLayer( layer, False )
                    args[v.identifier] = layer
                    
            elif parm.__class__.__name__ == 'ParameterExtent':
                coords = v.getValue().coords
                args[v.identifier] = str(coords[0][0])+','+str(coords[1][0])+','+str(coords[0][1])+','+str(coords[1][1])
            else:
                args[v.identifier] = v.getValue()
        # Adds None for output parameter(s)
        for k in self._outputs:
            v = getattr(self, k)
            args[v.identifier] = None
        
        if not len( self.alg.parameters ):
            self.alg.defineCharacteristics()

        tAlg = Processing.runAlgorithm(self.alg, None, args)
        # if runalg failed return exception message
        if not tAlg:
            return 'Error in processing'
        # clear map layer registry
        mlr.removeAllMapLayers()
        # get result
        result = tAlg.getOutputValuesAsDictionary()
        for k in self._outputs:
            v = getattr(self, k)
            parm = self.alg.getOutputFromName( v.identifier )
            if parm.__class__.__name__ == 'OutputVector':
                outputName = result.get(v.identifier, None)
                if not outputName :
                  return 'No output file'
                # get output file info
                outputInfo = QFileInfo( outputName )
                # get the output QGIS vector layer
                outputLayer = QgsVectorLayer( outputName, outputInfo.baseName(), 'ogr' )
                # create the output GML file for pywps
                # define the output GML file path
                outputFile = os.path.join( outputInfo.absolutePath(), outputInfo.baseName()+'.gml' )
                # write the output GML file
                error = QgsVectorFileWriter.writeAsVectorFormat( outputLayer, outputFile, 'utf-8', None, 'GML', False, None, ['XSISCHEMAURI=http://schemas.opengis.net/gml/2.1.2/feature.xsd'] )
                args[v.identifier] = outputFile
                # add output layer to map layer registry
                #outputLayer = QgsVectorLayer( outputFile, v.identifier, 'ogr' )
                #mlr.addMapLayer( outputLayer )
            elif parm.__class__.__name__ == 'OutputRaster':
                if not outputName :
                  return 'No output file'
                args[v.identifier] = result.get(v.identifier, None)
            else:
                args[v.identifier] = result.get(v.identifier, None)
        for k in self._outputs:
            v = getattr(self, k)
            v.setValue( args[v.identifier] )
        return

    try:
	    new_class = classobj( '%sProcess' % class_name, (WPSProcess, ), {
                '__init__' :  process_init,
	        'execute' : execute,
	        'params' : [],
	        'alg' : alg,
	        '_inputs' : {},
	        '_outputs' : {}
	    })
	    return new_class
    except TypeError, e:
        #logging.info('TypeError %sProcess: %s' % (class_name, e))
        return None

# get the providers to publish
providerList = config.getConfigValue( 'qgis', 'providers' )
if providerList :
    providerList = providerList.split(',')
    
# get the algorithm list to publish
algList = config.getConfigValue( 'qgis', 'algs' )
if algList :
    algList = algList.split(',')

# get the algorithm filter
# Set text to None to add all the QGIS Processing providers
algsFilter = config.getConfigValue( 'qgis', 'algs_filter' ) #'random' #'modeler:' #None
idx = 1
for provider in Processing.providers:
    if providerList and provider.getName() not in providerList :
        #logging.info( provider.getName()+' not render')
        continue
    # verify if the provider is activated
    if not ProcessingConfig.getSetting( 'ACTIVATE_' + provider.getName().upper().replace(' ', '_') ):
        #logging.info( provider.getName()+' not active')
        continue
    # verify if the provider is well installed
    if provider.getName() == 'saga':
        from processing.algs.saga.SagaUtils import SagaUtils
        msg = SagaUtils.checkSagaIsInstalled()
        if msg:
            logging.info(msg)
            continue
    elif provider.getName() == 'r':
        from processing.algs.r.RUtils import RUtils
        msg = RUtils.checkRIsInstalled()
        if msg:
            logging.info(msg)
            continue
    elif provider.getName() == 'grass':
        from processing.algs.grass.GrassUtils import GrassUtils
        msg = GrassUtils.checkGrassIsInstalled()
        if msg:
            logging.info(msg)
            continue
    elif provider.getName() == 'grass7':
        from processing.algs.grass.Grass7Utils import Grass7Utils
        msg = Grass7Utils.checkGrass7IsInstalled()
        if msg:
            logging.info(msg)
            continue
    #logging.info( provider.getName()+' active and install')
    # sort algorithms
    sortedlist = sorted(provider.algs, key=lambda alg: alg.name)
    for alg in sortedlist:
        if algList and str( alg.commandLineName() ) not in algList :
            continue;
        # filter with text
        if not algsFilter or algsFilter.lower() in alg.name.lower() or algsFilter.lower() in str( alg.commandLineName() ):
            #logging.info(alg.commandLineName())
            globals()['algs%s' % idx] = QGISProcessFactory( str( alg.commandLineName() ) )
            idx += 1
