#!/usr/bin/python
#
# Original implementation by Wintermute0110 <wintermute0110@gmail.com> 2017-03-16
#
# Information of lumps in a WAD
# Complements listmaps.py
#
import sys
import os
import pprint

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
    print('Omgifol script: lump information on a WAD file')
    print('List the lumps found on a WAD file')
else:
    print('Loading WAD "{0}" ...'.format(sys.argv[1]))
    inwad = WAD()
    inwad.from_file(sys.argv[1])
    # print('>>>>> inwad object')
    # pprint.pprint(vars(inwad))
    # print('>>>>> maps object')
    # pprint.pprint(vars(inwad.maps))
    # print('>>>>> groups object')
    # pprint.pprint(inwad.groups)
