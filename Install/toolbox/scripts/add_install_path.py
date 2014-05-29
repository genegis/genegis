import sys
import os

# enable local imports; redirect config calls to general config
def add_install_path():
    local_path = os.path.dirname(__file__)
    add_paths = [
            local_path, # scripts/
            os.path.join(local_path, '..',), # toolbox/
            os.path.join(local_path, '..', '..'), # Install/
            os.path.join(local_path, '..', 'lib') # Install/lib/
    ]
    for path in add_paths:
        full_path = os.path.abspath(path)
        sys.path.insert(0, full_path)

# pull config from parent project
add_install_path()
