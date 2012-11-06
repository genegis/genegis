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
# Required Inputs: A point Feature Class containing one IndividualID, exported from Encounter
#                  A destination Feature Class
#                  A personal gdb with Encounter and an empty f_Track to use as the template
#
# Script Outputs: A polyline Feature Class
#
# This script was developed to work with ArcGIS 10.1 and Python 2.7.3

import arcpy
import os
import types
import sys
import traceback

def convertPoints():
    arcpy.env.overwriteOutput = True

    #inPts = arcpy.GetParameterAsText(0)
    inPts  = "C:\\Documents and Settings\\tomas.follett\\My Documents\\ArcGIS\\Default.gdb\\Encounters420027"
    #outFeatures = arcpy.GetParameterAsText(1)
    outFeatures = "C:\\Documents and Settings\\tomas.follett\\My Documents\\ArcGIS\\Default.gdb\\Lines420027z"
    pointsToAttribLines(inPts, outFeatures)

def calcSpeed(segment, fromTime, currTime):
    try:
        distance = segment.getLength("GEODESIC")/1000.0
        delta = currTime - fromTime
        elapsed = (delta.days*60.0)+(delta.seconds/3600.0)
        speed = distance/elapsed
    except Exception as err:
        arcpy.AddError(err[0])

    finally:
        return [distance, elapsed, speed]

def pointsToAttribLines(inPts, outFeatures):
    spatialRef = inPts
    try:
        ## Assign empty values to cursor and row objects
        insCur, sRow = None, None

        ## Create the output feature class
        outPath, outFC = os.path.split(outFeatures)
        template = outPath+"\\f_Track"
        arcpy.CreateFeatureclass_management(outPath, outFC, "POLYLINE", \
                template, "SAME_AS_TEMPLATE", "DISABLED", inPts)

        ## Open an insert cursor for the new feature class
        insertFields = ["SHAPE@", "FeatureID", "FeatureCode", "StartDate", 
                        "EndDate", "FromLocation", "ToLocation", 
                        "IndividualID", "Distance", "Elapsed", 
                        "Speed", "CruiseID"]
        insCur = arcpy.da.InsertCursor(outFeatures, insertFields)

        ## Create an empty array to hold the geometry
        array = arcpy.Array()

        ## Set up SearchCursor for input points
        orderClause = [None, 'ORDER_BY "TimeValue"']
        selectedColumns = ["SHAPE@XY", "FeatureID", "TimeValue", \
                           "FromLocation", "IndividualID", "CruiseID"]
        with arcpy.da.SearchCursor(inPts, selectedColumns, None, spatialRef, \
                False, sql_clause = orderClause) as searchCur:
            ## Count the rows to use as a FeatureID
            rowID = -1
            for sRow in searchCur:
                if rowID == -1:
                    ## 1st row
                    rowID = 0
                    ## store point geometry
                    x, y = sRow[0]
                    currPoint = arcpy.Point(x, y)
                    array.add(currPoint)
                    ## store field values
                    currFeat = sRow[1] #FeatureID
                    currTime = sRow[2] #TimeValue
                    currLoc = sRow[3]  #FromLocation
                    currInd = sRow[4]  #IndividualID
                    currCru = sRow[5]  #CruiseID
                if rowID >0:
                    ## each subsequent row
                    x, y = sRow[0]
                    currPoint = arcpy.Point(x, y)
                    array.add(currPoint)
                    ## construct a path from the two points in the array
                    segment = arcpy.Polyline(array, spatialRef, False, True)
                    ## store previous and new field values
                    fromFeat = currFeat
                    currFeat = sRow[1]
                    fromTime = currTime
                    currTime = sRow[2]
                    fromLoc = currLoc
                    currLoc = sRow[3]
                    ## use the two point featureID's as the FeatureCode
                    featCode = str(fromFeat) + ", " + str(currFeat)
                    ## calculate values in correct units
                    distance, elapsed, speed = calcSpeed(segment, fromTime, currTime)
                    insCur.insertRow([segment, rowID, featCode, fromTime, 
                        currTime, fromLoc, currLoc, currInd, distance, 
                        elapsed, speed, currCru])
                    ## drop the 1st point
                    array.remove(0)
                rowID +=1
    except Exception as err:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        print tbinfo
        print "exception occured"
        arcpy.AddError(err)
        arcpy_messages = arcpy.GetMessages()
        arcpy.AddError(arcpy_messages)

    finally:
        if insCur: del insCur
        if sRow: del sRow

try:
    ## Update the spatial index(es)
    r = arcpy.CalculateDefaultGridIndex_management(outFeatures)
    arcpy.AddSpatialIndex_management(outFeatures, r.getOutput(0), r.getOutput(1), r.getOutput(2))
except:
    pass

if __name__ == '__main__':
    convertPoints()
