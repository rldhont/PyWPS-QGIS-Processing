#!/bin/sh

# Author: René-Luc D'Hont
# Purpose: CGI script for wrapping PyWPS script
# Licence: GNU/GPL
# Usage: Put this script to your web server cgi-bin directory, e.g.
# After adaptation
# /usr/lib/cgi-bin/ and make it executable (chmod 755 pywps.cgi)

# NOTE: tested on linux/apache

# Need a virtuam display
# you can create one with: Xvfb :99 -ac -noreset &
export DISPLAY=:99
# Python path to the QGIS python share and QGIS python plugins share
# you can add your plugins directory
export PYTHONPATH=/usr/share/qgis/python:/usr/share/qgis/python/plugins #:/home/user/.qgis2/python/plugins
# Ld Library Path
export LD_LIBRARY_PATH=/usr/lib #:/path/to/qgis/lib if not default
# PyWPS config
export PYWPS_CFG=/path/to/pywps/wps/pywps.cfg
# PyWPS processes directory
export PYWPS_PROCESSES=/path/to/pywps/wps/processes/
# PyWPS wps python script
/path/to/PyWPS/wps.py
