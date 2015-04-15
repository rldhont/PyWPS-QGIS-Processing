PyWPS-QGIS-Processing
======================

This is a way to bring at least part of QGIS Processing
Functionality to World Wide Web Through WPS.

INSTALL embedded PyWPS
-----------------------

You will install pywps the quick and dirty way :

1. cd to PyWPS-QGIS-Processing directory:

    $ cd /home/foo/bar/PyWPS-QGIS-Processing
    
2. Simply copy PyWPS directory to the target directory:

    $ cp PyWPS /usr/local/


We used an embedded PyWPS because we updated it to initialize a QGIS environment for QGIS-Processing and to use QGIS-Server for as reference outputs

For more information about PyWPS : http://pywps.wald.intevation.org/documentation/

INSTALL PyWPS-QGIS-Processing
-----------------------------

PyWPS-QGIS-Processing comes with :

1. pywps.cgi
2. pywps.cfg
3. processes

Update **pywps.cgi** to adapt it to your PyWPS and QGIS install :

* **DISPLAY**, you need to create a virtual display for example with Xvfd
* **PYTHONPATH** to your QGIS install and the plugins directories
* **LD_LIBRARY_PATH** to your QGIS install
* **PYWPS_CFG** to the path where you put the PyWPS-QGIS-Processing pywps.cfg
* **PYWPS_PROCESSES** to the directory path where you put PyWPS-QGIS-Processing processes directory
* the path to the PyWPS wps python script

Update **pywps.cfg** like it's describe in PyWPS install.

We add two section to **pywps.cfg** to configure PyWPS-QGIS-Processing :

* \[qgis\]

  * **prefix** path to your QGIS installation. The QGIS installation directory contains *lib* and *share* directory
  * **user_folder** path to the folder where QGIS Processing will generate *log* and *temporary* files. For QGIS Desktop, this directory is */home/user/.qgis2*
  * **providers** the providers list separated by comma you want to publish. The list can contain *qgis,gdalogr,script,model,r,grass,grass70,saga*. If the list is empty all providers will be published
  * **algs_filter** text to filter algorithms. Text will be searched in algorithm name and commandLineName
  * **algs** an algorithms white list  separated by comma you want to publish. Algorithms are defined by their commandLineName, for example *qgis:voronoipolygons,qgis:fixeddistancebuffer,gdalogr:aspect,gdalogr:hillshade,gdalogr:roughness,gdalogr:slope,gdalogr:contour*
  * **projects_folder** path to the directory which contains qgis projects. You can defined a project by algorithms to provide complex input data.
  * **qgisserveraddress** the QGIS-Server address to publish outputs as webservices

* \[qgis_processing\]

  * the __ACTIVE_*__ activate providers, you can *activate providers* without publishing them if they are needed in models
  * the __*_FOLDER__ for the pathes to your *models*, *scripts* and *R* scripts
  * the __SAGA_*__ are for the SAGA provider configuration
  * all the providers configuration parameters can be done here.

* Copy :

  * **models** form your QGIS Processing models to the \[qgis_processing\] **MODELS_FOLDER**
  * **scripts** form your QGIS Processing scripts to the \[qgis_processing\] **SCRIPTS_FOLDER**
  * **rscripts** from your R QGIS Processing to the \[qgis_processing\] **R_FOLDER**

By default PyWPS-QGIS-Processing provide a model **modeler:buffer** which is a simplification of the process **qgis:fixeddistancebuffer**

Once all is conform to your PyWPS and QGIS installation you can open the links :

* http://localhost/cgi-bin/pywps.cgi?SERVICE=WPS&REQUEST=GetCapabilities
* http://localhost/cgi-bin/pywps.cgi?SERVICE=WPS&VERSION=1.0.0&REQUEST=describeprocess&IDENTIFIER=modeler:buffer
* http://localhost/cgi-bin/pywps.cgi?SERVICE=WPS&VERSION=1.0.0&REQUEST=execute&IDENTIFIER=modeler:buffer&DATAINPUTS=\[NUMBER_DIST=20.0;VECTORLAYER_BASE=http://apps.esdi-humboldt.cz/classification/traning_areas/training_areas_en.gml]

