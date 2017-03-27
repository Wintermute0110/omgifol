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
    wad = WAD()
    wad.from_file(sys.argv[1])

    # print('>>>>> inwad object')
    # pprint.pprint(vars(wad))
    # print('>>>>> maps object')
    # pprint.pprint(vars(wad.maps))
    # print('>>>>> groups object')
    # pprint.pprint(wad.groups)

    print('--- Graphics ---')
    print('Number of sprites   {0:5d}'.format(len(wad.sprites)))
    print('Number of patches   {0:5d}'.format(len(wad.patches)))
    print('Number of flats     {0:5d}'.format(len(wad.flats)))
    print('Number of graphics  {0:5d}'.format(len(wad.graphics)))    
    print('Number of colormaps {0:5d}'.format(len(wad.colormaps)))
    print('Number of ztextures {0:5d}'.format(len(wad.ztextures)))
    print('Number of txdefs    {0:5d}'.format(len(wad.txdefs)))
    print('--- Music and sounds ---')
    print('Number of music     {0:5d}'.format(len(wad.music)))
    print('Number of sounds    {0:5d}'.format(len(wad.sounds)))
    print('--- Misc data ---')
    print('Number of data      {0:5d}'.format(len(wad.data)))
    print('--- Level data ---')
    print('Number of maps      {0:5d}'.format(len(wad.maps)))
    print('Number of glmaps    {0:5d}'.format(len(wad.glmaps)))

    # >> List lumps
    # print('[Graphics lump name list]')
    # for lump_name in wad.graphics: print(lump_name)
    # print('[Map name list]')
    # for lump_name in wad.maps: print(lump_name)
