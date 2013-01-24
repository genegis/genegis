#PointsToAttributedLines.py
#
# Created by: T Follett
#             Marine Mammal Institute
#             Oregon State Univeristy
#
# Created on: 30 Oct 2012
# Last modified: 6 Nov 2012
# 
# Description: This script takes a set of points from a single individual and creates a polyline with attributes 
#              from the source points, as well as distance in Km, elapsed time in Hrs, and speed in Km/hr
#               
# Required Inputs: A point Feature Class containing one IndividualID, exported from Encounter
#                  A destination Feature Class
#                  A personal gdb with Encounter and an empty f_Track to use as the template
#
# Script Outputs: A line Feature Class
#              
# This script was developed to work with ArcGIS 10.1 and Python 2.7.3

import arcpy
import os
import types
import sys
import traceback

def convertPoints():
    inPts       = arcpy.GetParameterAsText(0)
    outFeatures = arcpy.GetParameterAsText(1)
    pointsToAttribLines(inPts, outFeatures)

def calcSpeed(segment, fromTime, currTime):
    try:
		# convert meters to kilometers
        distance = segment.getLength("GEODESIC")/1000.0    
		# subtraction returns a TimeDelta object in format of (days, seconds)
        delta = currTime - fromTime                        
        # convert TimeDelta values into hours and add together (force decimal)
		elapsed = (delta.days*60.0)+(delta.seconds/3600.0)
		# derive speed
        speed = distance/elapsed
    except Exception as err:
        arcpy.AddError(err[0])

    finally:
        return [distance, elapsed, speed]


def pointsToAttribLines(inPts, outFeatures):
    spatialRef = arcpy.Describe(inPts).spatialReference

    try:
        ## Assign empty values to cursor and row objects
        insCur, sRow = None, None

        ## Prepare to create new Feature class
        uniqueFC = arcpy.CreateUniqueName(outFeatures)
        outPath, outFC = os.path.split(uniqueFC)
        template = outPath+u"\\f_Track"        
        ## Create the output Feature class
        arcpy.CreateFeatureclass_management(outPath, outFC, "POLYLINE", \
                                            template, "DISABLED", "DISABLED", spatialRef) 

        ## Open an insert cursor for the new feature class
        insertFields = ["SHAPE@", "FeatureID", "FeatureCode", "StartDate", 
                        "EndDate", "FromLocation", "ToLocation", 
                        "IndividualID", "Distance", "Elapsed", 
                        "Speed", "CruiseID"]
        insCur = arcpy.da.InsertCursor(uniqueFC, insertFields)

        ## Set up SearchCursor for input points       
        orderClause = [None, 'ORDER BY "TimeValue"']
        with arcpy.da.SearchCursor(inPts, ["SHAPE@XY", "FeatureID", "TimeValue", 
                                           "FromLocation", "IndividualID", "CruiseID"], None, spatialRef , 
                                            False, sql_clause = orderClause) as searchCur:
            ## Count the rows and use as the FeatureID value
            rowID = -1
            for sRow in searchCur:
                if rowID == -1: ## 1st row
                    rowID = 0
                    ## store points
                    x, y = sRow[0]
                    currPoint = arcpy.Point(x, y) #(Stores M), None, sRow[3])
                    array = arcpy.Array(currPoint)
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
                    ## construct a path using the two points in the array
                    segment = arcpy.Polyline(array, spatialRef, False, False)
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
                    ## add path to feature class
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
        print u"exception occured"
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