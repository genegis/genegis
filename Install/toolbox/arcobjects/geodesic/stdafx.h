// stdafx.h : include file for standard system include files,
// or project specific include files that are used frequently, but
// are changed infrequently
//

#pragma once

#include "targetver.h"

#include <fstream>
#include <iostream>

#define WIN32_LEAN_AND_MEAN             // Exclude rarely-used stuff from Windows headers
// Windows Header Files:
#include <windows.h>



// Type libraries for consuming ArcObjects
#import "esriSystem.olb" raw_interfaces_only, raw_native_types, no_namespace, named_guids, exclude("OLE_COLOR", "OLE_HANDLE", "VARTYPE")
#import "esriGeometry.olb" raw_interfaces_only, raw_native_types, no_namespace, named_guids
#import "esriGeoDatabase.olb" raw_interfaces_only, raw_native_types, no_namespace, named_guids
#import "esriGeoprocessing.olb" raw_interfaces_only, raw_native_types, no_namespace, named_guids
