geneGIS 
=======

A Python Add-in and ArcGIS toolbox for manipulating individual-based genetic records in a geographic context.

[http://genegis.org](http://genegis.org)


Installation
------------

Use the [install page](http://genegis.org/install.html) to get a packaged release.

To get the latest source, clone this repository, and run `makeaddin.py` to create an
installable genegis.esriaddin file.

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
 - use SPAGeDi (included) to compute a variety of genetic tests, such as `F_st`.

export:
 - export to GenAlEx
 - export to Genepop
 - export to SPAGeDi
 - export to SRGD formatted CSV files for use with the Shepard Project

Building from Source
--------------------

```
git clone --recursive https://github.com/genegis/genegis.git
```

Development
-----------

[Nose](https://nose.readthedocs.org/en/latest/) tests are included which perform basic checks. To run, the tests, use `pip` to install requirements:
    
    $ pip install -r requirements-dev.txt

Then, run nose from the top-level directory:

    $ nosetests


