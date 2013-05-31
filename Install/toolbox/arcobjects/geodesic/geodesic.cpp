// geodesic.cpp : Compute true geodestic distance matrix.
// Shaun Walbridge
// Esri
// 2013.05.31

#include "stdafx.h"

extern "C"
{

  __declspec(dllexport) int CalculatePairwiseGeodesicDistances(const wchar_t* feature_class, const wchar_t* output_file)
  {
	  // FIXME: write to selected output file
	  std::ofstream fs(output_file);
      if (!fs)
	  {
		  std::cerr<<"Cannot open the output file."<<std::endl;
		  return -1;
	  }
	  // Convert wchar_t*s to bstring
	  _bstr_t catalogPath(feature_class);

	  // Coinitialize GP utilities class
	  IGPUtilitiesPtr ipUtil(CLSID_GPUtilities);

	  // Feature class holder
	  IFeatureClassPtr ipFeatureclass(0);

	  HRESULT hr;

	  // Try to fetch feature class from catalog path
	  if (FAILED(hr = ipUtil->OpenFeatureClassFromString(catalogPath, &ipFeatureclass)))
		  return -2;

	  // Set up query and filter
	  IQueryFilterPtr ipFilter(CLSID_QueryFilter);
	  IFeatureCursorPtr ipCursor;
	  IFeaturePtr ipRow;
	  IGeometryPtr ipGeometry;
	  esriGeometryType gt;

	  // coordinate system
      IGeographicCoordinateSystemPtr pGCS;
      ISpatialReferenceFactoryPtr pSpatRefFactory(CLSID_SpatialReferenceEnvironment);
	  ISpatialReferencePtr spatialReference;
	  // use meters as default linear units
	  IUnitPtr ipUnit;
      pSpatRefFactory->CreateUnit(esriSRUnit_Meter, &ipUnit);
	  ILinearUnitPtr linearUnit = ipUnit;

	  // get the feature count to initialize our output matrix
	  long featureCount;
      ipFeatureclass->FeatureCount(NULL, &featureCount);
	  // initialize the 2d matrix (array of pointers)
      double** matrix = new double*[featureCount];
      IPointArrayPtr ipPointArray;
	  ipPointArray.CreateInstance(CLSID_PointArray);

	  // FIXME: REPLACE THIS WITH THE TRUE 'ID' field.
      long* oids = new long[featureCount];

	  // Currently, this is only set to run as a 32-bit process, and
	  // it'll crash if the application tries to use more than ~1.5GB
	  // of memory. Approximate the dimensions that we'd expect to work
	  // and fail if the user exceeds these limits.
	  int arrayMemUsage = 8 * (featureCount**2) / (1024**2);
	  if (arrayMemUsage > 1200)
		  return -3;

	  // Open search cursor on feature class
	  ipFeatureclass->Search(ipFilter, VARIANT_FALSE, &ipCursor);
	  int i = 0;
	  for (ipCursor->NextFeature(&ipRow);
		     ipRow != NULL;
		     ipCursor->NextFeature(&ipRow))
	  {
		  // FIXME: REPLACE THIS WITH THE TRUE 'ID' field.
		  long oid_val;
		  ipRow->get_OID(&oid_val);
		  oids[i] = oid_val;

		  ipRow->get_Shape(&ipGeometry);
		  IPointPtr ipPoint (ipGeometry);
		  if (i == 0)
		  {
			  // make sure inputs are points
		      ipGeometry->get_GeometryType(&gt);
			  if (gt != esriGeometryPoint)
				  return -3;
		  }
          // push the point onto our array of 
          ipPointArray->Add(ipPoint);

		  // initialize output matrix element for this point
          matrix[i] = new double[featureCount];
		  i++;
	  }

      // geometry server
	  IGeometryServer2Ptr geomServer;
	  geomServer.CreateInstance(CLSID_GeometryServerImpl);	  

      IRelationalOperatorPtr ipRelOp;

	  double distance;
	  for (int i = 0; i < featureCount; i++)
	  {
		  //fs << "at distance calculation for row " << i << std::endl;
          IPointPtr ipPointFrom;
	      IPointPtr ipPointTo;
		  //fs << coord_vals[i][1] << "," << coord_vals[i][2] << "(typeid: " << typeid(coord_vals[i][2]).name() << std::endl;
		  ipPointFrom.CreateInstance(CLSID_Point);
		  ipPointTo.CreateInstance(CLSID_Point);

          ipPointArray->get_Element(i, &ipPointFrom);

		  // set up a relational operator for this point
		  ipRelOp = ipPointFrom;

		  for (int j = 0; j < featureCount; j++) 
		  {
			  if (i == j)
			  {
				  distance = 0;
			  }
			  else if (matrix[j][i] > 0) 
			  {
				  //fs << "matrix[j][i] is not NULL, value is `" << matrix[j][i] << "`, type " << typeid(matrix[j][i]).name() << std::endl;
				  distance = matrix[j][i];
			  }
			  else
			  {
			      ipPointArray->get_Element(j, &ipPointTo);

                  VARIANT_BOOL bEquals;
			      ipRelOp->Equals(ipPointTo, &bEquals);

			      if (bEquals)
			      {
			          distance = 0;
			      }
			      else
			      { 
					  //fs << "try to get geodesic distance..." << std::endl;
				      geomServer->GetDistanceGeodesic(spatialReference, ipPointFrom, ipPointTo, linearUnit, &distance);
				  }
			  }
			  matrix[i][j] = distance;
		  }
	  }

	  // write header row
	  for (int h = 0; h < featureCount; h++)
	  {
		  fs << "," << oids[h];
	  }
	  fs << std::endl;

	  // write out results
      for (int i = 0; i < featureCount; i++) 
	  {
		  fs << oids[i] << ",";
          for (int j = 0; j < featureCount - 1; j++) 
		  {
			  fs << std::fixed << matrix[i][j] << ",";
		  }
		  fs << std::fixed << matrix[i][featureCount - 1] << std::endl;
	  }
      fs.close();
	  return 0;
  }

}
