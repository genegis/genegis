#!/usr/bin/bash
echo "building Addin..."
python ./makeaddin.py
echo "signing Addin..."
# "/c/Program Files (x86)/Common Files/ArcGIS/bin/ESRISignAddin.exe" c:\\data\\arcgis\\addins\\genegis\\genegis.esriaddin /c/ssh/id_rsa.ppk
# start /c/Users/shau7031/Documents/ArcGIS/genegis.mxd
start ~/Documents/ArcGIS/genegis.mxd
