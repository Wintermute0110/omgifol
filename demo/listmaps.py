#!/usr/bin/python
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
    print('Omgifol script: list maps on a WAD file')
    print('List the maps found on a WAD file')
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

    print('Number of levels {0}'.format(inwad.maps._n))
    for i, name in enumerate(inwad.maps):
        edit = MapEditor(inwad.maps[name])
        # print('>>>>> map object')
        # pprint.pprint(vars(inwad.maps[name]))
        # print('>>>>> edit object attribute keys')
        # pprint.pprint(edit.__dict__.keys())
        print('Map number {0:2d} name {1}'.format(i, name))
        print('  Things   {0:5d}'.format(len(edit.things)))
        print('  Vertexes {0:5d}'.format(len(edit.vertexes)))
        print('  Linedefs {0:5d}'.format(len(edit.linedefs)))
        print('  Sidedefs {0:5d}'.format(len(edit.sidedefs)))
        print('  Sectors  {0:5d}'.format(len(edit.sectors)))
        # print('  Nodes    {0:5d}'.format(len(edit.nodes)))
