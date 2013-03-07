#!/usr/bin/bash
echo "building Addin..."
python ./makeaddin.py
echo "signing Addin..."
/c/apps/arcgis/Desktop10.1/bin/ESRISignAddin.exe c:\\data\\arcgis\\addins\\genegis\\genegis.esriaddin /c:c:\\data\\arcgis\\addins\\cert.cer
start genegis.esriaddin
start /c/Users/shau7031/Documents/ArcGIS/genegis.mxd
