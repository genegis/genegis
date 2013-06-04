geneGIS 
=======

A Python Add-in and ArcGIS toolbox for manipulating individual-based genetic records in a geographic context.

[http://genegis.org](http://genegis.org)

Tools
-----

import:
 - parse SRGD formatted CSV files into a Geodatabase Feature Class

manipulation:
 - select and filter data based on spatial and attribute queries
 - extract raster values at encounter locations
 
geographic analysis:
 - compute accurate geodesic distance matricies
 - generate pairwise geodesic segements between samples
 
genetic analysis:
 - use SPAGeDi (included) to compute a variety of genetic tests, such as F_st.

export:
 - export to GenAlEx
 - export to Genepop
 - export to SPAGeDi
 - export to SRGD formatted CSV files for use with the Shepard Project
