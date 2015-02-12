PyWPS-QGIS-Processing
======================

This is a way to bring at least part of QGIS Processing
Functionality to World Wide Web Through WPS.

INSTALL PyWPS
-------------

You can install pywps the quick and dirty way :

1. Download from http://pywps.wald.intevation.org/download/index.html
2. cd to target directory:

    $ cd /usr/local/

3. unpack pywps:

    tar xvzf /tmp/pywps-VERSION.tar.gz

For more information about PyWPS install : http://pywps.wald.intevation.org/documentation/installation.html

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

  * *prefix* path to your QGIS install
  * *user_folder* path to the folder where QGIS Processing will generate temporary files
  * *providers* the providers list separated by comma you want to publish
  * *algs_filter* text to filter algorithms

* \[qgis_processing\]

  * the *ACTIVE_\** activate providers, you can activate providers without publishing them if they are needed in models
  * the *\*_FOLDER* for the pathes to your models, scripts and R scripts
  * the *SAGA_\** are for the SAGA provider configuration
  * all the providers configuration parameters can be done here.

* add :

  * **models** form your QGIS Processing models
  * **scripts** form your QGIS Processing scripts
  * **rscripts** from your R QGIS Processing

By default PyWPS-QGIS-Processing provide a model **modeler:buffer** which is a simplification of the process **qgis:fixeddistancebuffer**

Once all is conform to your PyWPS and QGIS installation you can open the links :

* http://localhost/cgi-bin/pywps.cgi?SERVICE=WPS&REQUEST=GetCapabilities
* http://localhost/cgi-bin/pywps.cgi?SERVICE=WPS&VERSION=1.0.0&REQUEST=describeprocess&IDENTIFIER=modeler:buffer
* http://localhost/cgi-bin/pywps.cgi?SERVICE=WPS&VERSION=1.0.0&REQUEST=execute&IDENTIFIER=modeler:buffer&DATAINPUTS=\[NUMBER_DIST=20.0;VECTORLAYER_BASE=http://apps.esdi-humboldt.cz/classification/traning_areas/training_areas_en.gml\]

