#PointsToAttributedLines.py
#
# Created by: T Follett
#             Marine Mammal Institute
#             Oregon State Univeristy
#
# Created on: 31 Oct 2012
# Last modified: 31 Oct 2012
# 
# Description: This script takes a set of points from a single individual and creates a polyline with attributes 
#              from the source points as well as distance in Km, elapsed time in hours, and speed in Km/hr
#               
# Required Inputs: A point Feature Class created by selecting one IndividualID from Encounter
#                  A destination Feature Class
#
# Script Outputs: A polyline Feature Class
#              
# This script was developed to work with ArcGIS 10.1 and Python 2.7.3

import arcpy
import os
import types

def convertPoints():
  arcpy.env.overwriteOutput = True
  #inPts       = arcpy.GetParameterAsText(0)
  inPts       = "C:\\Documents and Settings\\tomas.follett\\My Documents\\ArcGIS\\Default.gdb\\Encounters420027"
  #outFeatures = arcpy.GetParameterAsText(1)
  outFeatures = "C:\\Documents and Settings\\tomas.follett\\My Documents\\ArcGIS\\Default.gdb\\Lines420027z"
  pointsToAttribLines(inPts, outFeatures)

def calcSpeed(segment, fromTime, currTime):
  try:
    distance = segment.getLength("GEODESIC")/1000.0
    delta = currTime - fromTime
    daysHrs = delta.days*60.0
    secsHrs = delta.seconds/3600.0
    elapsed = daysHrs+secsHrs
    speed = distance/elapsed
  except Exception as err:
    arcpy.AddError(err[0])
    
  finally:
    return [distance, elapsed, speed]

def pointsToAttribLines(inPts, outFeatures):
  #if arcpy.Exists(outFeatures):
    #arcpy.Delete_management(outFeatures)
  spatialRef = inPts
  try:
    ## Assign empty values to cursor and row objects
    insCur, sRow = None, None
    ## Create the output feature class
    outPath, outFC = os.path.split(outFeatures) # Separate the path from the name
    template = outPath+"\\f_Track"
    arcpy.CreateFeatureclass_management(outPath, outFC, "POLYLINE", template, "SAME_AS_TEMPLATE", "DISABLED", inPts) 
    ## Open an insert cursor for the new feature class
    insertFields = ["SHAPE@", "FeatureID", "FeatureCode", "StartDate", "EndDate",
                    "FromLocation", "ToLocation", "IndividualID", "Distance", "Elapsed", "Speed", "CruiseID"]
    insCur = arcpy.da.InsertCursor(outFeatures, insertFields)
    ## Create an empty array to hold the geometry
    array = arcpy.Array()
    # Fix this syntax to include in search cursor
    #orderClause = [None, 'ORDER_BY "TimeValue"']
    ##Set up SearchCursor for input points                  
    with arcpy.da.SearchCursor(inPts, ["SHAPE@XY", "FeatureID", "TimeValue", "FromLocation", 
                                       "IndividualID", "CruiseID"], "",None , False) as searchCur:
      rowID = -1
      for sRow in searchCur:
        if rowID == -1: 
          rowID = 0
          #1st point geometry
          x, y = sRow[0]
          currPoint = arcpy.Point(x, y) 
          array.add(currPoint)
          #1st field values
          currFeat = sRow[1] #FeatureID
          currTime = sRow[2] #TimeValue
          currLoc = sRow[3] #FromLocation
          currInd = sRow[4] #IndividualID
          currCru = sRow[5] #CruiseID
        if rowID >0:
          x, y = sRow[0]
          currPoint = arcpy.Point(x, y)
          array.add(currPoint)
          segment = arcpy.Polyline(array, spatialRef, False, True)
          fromFeat = currFeat
          currFeat = sRow[1]
          fromTime = currTime
          currTime = sRow[2]
          fromLoc = currLoc
          currLoc = sRow[3]
          featCode = str(fromFeat) + ", " + str(currFeat)
          distance, elapsed, speed = calcSpeed(segment, fromTime, currTime)
          insCur.insertRow([segment, rowID, featCode, fromTime, currTime, fromLoc, currLoc, currInd, distance, elapsed, speed, currCru])        
          array.remove(0) #Start point
        rowID +=1
        #Next row
  
  except Exception as err:
    arcpy.AddError(err[0])
  
  finally:
    if insCur: del insCur
    if sRow: del sRow
    #if array: del array

try:
  ## Update the spatial index(es)
  r = arcpy.CalculateDefaultGridIndex_management(outFeatures)
  arcpy.AddSpatialIndex_management(outFeatures, r.getOutput(0), r.getOutput(1), r.getOutput(2))
except:
  pass

if __name__ == '__main__':
    convertPoints()