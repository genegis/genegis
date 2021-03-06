// geodesic.cpp : Compute true geodestic distance matrix.
// Shaun Walbridge
// Esri
// 2013.05.31

#include "stdafx.h"

extern "C"
{

    __declspec(dllexport) int CalculatePairwiseGeodesicDistances(const wchar_t* feature_class, const wchar_t* output_file, const double unit_factor, const bool is_spagedi)
    {
        std::ofstream fs(output_file);
        if (!fs)
        {
            std::cerr << "Cannot open the output file." <<std::endl;
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
        {
            fs << "Failed to open: " << catalogPath << std::endl;
            return -2;
        }

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

        long* oids = new long[featureCount];

        // Currently, this is only set to run as a 32-bit process, and
        // it'll crash if the application tries to use more than ~1.5GB
        // of memory. Approximate the dimensions that we'd expect to work
        // and fail if the user exceeds these limits.
        double arrayMemUsage = (8.0 * pow((double)featureCount, 2)) / pow(1024.0,2);
        if (arrayMemUsage > 1200)
            return -3;

        // Open search cursor on feature class
        ipFeatureclass->Search(ipFilter, VARIANT_FALSE, &ipCursor);
        int i = 0;
        for (ipCursor->NextFeature(&ipRow);
             ipRow != NULL;
             ipCursor->NextFeature(&ipRow))
        {
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
                    return -4;
            }
            // push the point onto our array
            ipPointArray->Add(ipPoint);

            // initialize output matrix element for this point
            matrix[i] = new double[featureCount];
            i++;
        }

		// still have a poiner to the last referenced geometry, use
		// this to set the computation spatial reference.
		ipGeometry->get_SpatialReference(&spatialReference);
        
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
		
            // "(typeid: " << typeid(coord_vals[i][2]).name() << std::endl;
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
                    //fs << "matrix[j][i] is not NULL, value is `" << matrix[j][i] << 
                    // "`, type " << typeid(matrix[j][i]).name() << std::endl;
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
					    //double from_x, from_y, to_x, to_y;
			            //ipPointFrom->QueryCoords(&from_x, &from_y);
						//ipPointTo->QueryCoords(&to_x, &to_y);
						//fs << "dist from: (" << from_x << "," << from_y << ")" << 
						//	" to (" << to_x << "," << to_y << ") with sr `" <<
						//	spatialReference << "`, unit factor " << unit_factor << "." << std::endl;

                        geomServer->GetDistanceGeodesic(spatialReference, ipPointFrom, ipPointTo, linearUnit, &distance);
						// rescale distance by the unit factor (current unit releative to meters)
						distance = distance * unit_factor;
                    }
                }
                matrix[i][j] = distance;
            }
        }
        // two possible output formats: 'standard' and 'SPAGeDi'.

		const char sep = is_spagedi ? '\t' : ',';

		if (is_spagedi) {
			fs << "M" << featureCount << sep;
		}

        // write header row
        for (int h = 0; h < featureCount; h++)
        {
            fs << sep << oids[h];
        }
        fs << std::endl;

        // write out results
        for (int i = 0; i < featureCount; i++) 
        {
            fs << oids[i] << sep;
            for (int j = 0; j < featureCount - 1; j++) 
            {
                fs << std::fixed << matrix[i][j] << sep;
            }
            fs << std::fixed << matrix[i][featureCount - 1] << std::endl;
        }
		if (is_spagedi) {
			fs << "END" << std::endl;
		}
        fs.close();
        return 0;
    }
}
