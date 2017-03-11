#!/usr/bin/python
#
import sys
import os
from PIL import Image, ImageDraw

# --- Add OMG module to Python path ---
real_path  = os.path.realpath(__file__)
currentdir = os.path.dirname(real_path)
parentdir  = os.path.dirname(currentdir)
moduledir  = os.path.dirname(parentdir)
sys.path.insert(0, moduledir) 
from omg import *

# -------------------------------------------------------------------------------------------------
# main ()
# -------------------------------------------------------------------------------------------------
if len(sys.argv) < 2:
    print('Omgifol script: list maps on a WAD file')
    print('List the maps found on a WAD file')
else:
    print('Loading WAD "{0}" ...'.format(sys.argv[1]))
    inwad = WAD()
    inwad.from_file(sys.argv[1])
    for i, name in enumerate(inwad.maps):
        print('Map number {0:2d} name {1}'.format(i, name))
