#!/usr/bin/bash
echo "building Addin..."
python ./makeaddin.py
echo "signing Addin..."
"/c/Program Files (x86)/Common Files/ArcGIS/bin/ESRISignAddin.exe" Z:\\data\\arcgis\\addins\\genegis\\genegis.esriaddin /c:Z:\\data\\arcgis\\addins\\cert.cer
echo "Would you like to install the add-in? y/N"
read input
if [ "$input" == "y" ]; then
  start genegis.esriaddin
else
  echo 'skipping installation.'
fi

echo "Would you like to open the geneGIS MXD? y/N"
read input
if [ "$input" == "y" ]; then
  # start /c/Users/shau7031/Documents/ArcGIS/genegis.mxd
  start \\\\psf\\Home\\Documents\\ArcGIS\\genegis.mxd
else
  echo 'not opening MXD.'
fi
