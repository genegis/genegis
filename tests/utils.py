import os
import sys

def addLocalPaths(paths):
    for path_part in paths:
        base_path = os.path.join(os.path.dirname(__file__), path_part)
        abs_path = os.path.abspath(base_path)
        sys.path.insert(0, abs_path)

