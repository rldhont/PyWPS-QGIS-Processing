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
from xml.sax.saxutils import escape

QgsApplication( sys.argv, False, os.path.dirname( os.path.abspath( inspect.getfile( inspect.currentframe() ) ) ) )
# supply path to where is your qgis installed
QgsApplication.setPrefixPath( config.getConfigValue("qgis","prefix"), True )

# load providers
QgsApplication.initQgis()

# initialize application
qa = QApplication( sys.argv )

from processing.core.Processing import Processing
from processing.tools.general import *

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)
Processing.initialize()


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

    def process_init(self):
        # Automatically init the process attributes
        isText, help = self.alg.help()
        if not isText :
           with open(help, 'r') as helpFile :
              help = helpFile.read()
        WPSProcess.__init__(self,
            identifier=alg_name, # must be same, as filename
            title=escape(alg.name),
            version = "0.1",
            storeSupported = "true",
            statusSupported = "true",
            abstract= '<![CDATA[' + (help == None or str(alg) and help) + ']]>',
            grassLocation=False)
        self.alg = alg
        if not len( alg.parameters ):
            alg.defineCharacteristics()
        # Add I/O
        i = 1
        for parm in alg.parameters:
            if getattr(parm, 'optional', False):
                minOccurs = 0
            else:
                minOccurs = 1
            # TODO: create "LiteralValue", "ComplexValue" or "BoundingBoxValue"
            # this can be done checking the class:
            # parm.__class__, one of
            # ['Parameter', 'ParameterBoolean', 'ParameterCrs', 'ParameterDataObject', 'ParameterExtent', 'ParameterFile', 'ParameterFixedTable', 'ParameterMultipleInput', 'ParameterNumber', 'ParameterRange', 'ParameterRaster', 'ParameterSelection', 'ParameterString', 'ParameterTable','ParameterTableField', 'ParameterVector']
            if parm.__class__.__name__ == 'ParameterVector':
                self._inputs['Input%s' % i] = self.addComplexInput(parm.name, parm.description,
                    formats = [{'mimeType':'text/xml'}])
            elif parm.__class__.__name__ == 'ParameterRaster':
                self._inputs['Input%s' % i] = self.addComplexInput(parm.name, parm.description,
                    formats = [{'mimeType':'image/tiff'}])
            elif parm.__class__.__name__ == 'ParameterExtent':
                self._inputs['Input%s' % i] = self.addBBoxInput(parm.name, parm.description,
                    minOccurs=minOccurs)
            else:
                if parm.__class__.__name__ == 'ParameterBoolean':
                    type = types.BooleanType
                elif  parm.__class__.__name__ =='ParameterNumber':
                    type = types.FloatType
                else:
                    type = types.StringType
                self._inputs['Input%s' % i] = self.addLiteralInput(parm.name, parm.description,
                                                minOccurs=minOccurs,
                                                type=type,
                                                default=getattr(parm, 'default', None))
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
                if  parm.__class__.__name__ =='OutputNumber':
                    type = types.FloatType
                else:
                    type = types.StringType
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
        # Run alg with params
        # TODO: get args
        args = {}
        for k in self._inputs:
            v = getattr(self, k)
            parm = self.alg.getParameterFromName( v.identifier )
            if parm.__class__.__name__ == 'ParameterVector':
                fileName = v.getValue()
                logging.info( v.identifier+': '+str(fileName) )
                fileInfo = QFileInfo( fileName )
                # move fileName to fileName.gml for ogr
                with open( fileName, 'r' ) as f :
                    o = open( fileName+'.gml', 'w' )
                    o.write( f.read() )
                    o.close()
                # get layer
                layer = QgsVectorLayer( fileName+'.gml', fileInfo.baseName(), 'ogr' )
                args[v.identifier] = fileName+'.gml'
            else:
                args[v.identifier] = v.getValue()
        # Adds None for output parameter(s)
        for k in self._outputs:
            v = getattr(self, k)
            args[v.identifier] = None

        tAlg = Processing.runAlgorithm(self.alg, None, args)
        # if runalg failed return exception message
        if not tAlg:
            return 'Error in processing'
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

# Set text to None to add all the QGIS Processing providers
text = 'buffer' #None
idx = 1
for provider in Processing.algs.values():
    sortedlist = sorted(provider.values(), key=lambda alg: alg.name)
    for alg in sortedlist:
        if text is None or text.lower() in alg.name.lower() or text.lower() in str( alg.commandLineName() ):
            globals()['algs%s' % idx] = QGISProcessFactory( str( alg.commandLineName() ) )
            idx += 1
