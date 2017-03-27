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
    print('Num | Name  | Things | Vertexes | Linedefs | Sidedefs | Sectors |   Segs | SSectors | Nodes |')
    print('----|-------|--------|----------|----------|----------|---------|--------|----------|-------|')
    for i, name in enumerate(inwad.maps):
        edit = MapEditor(inwad.maps[name])
        # print('>>>>> inwad.maps[name] object')
        # pprint.pprint(vars(inwad.maps[name]))
        # print('>>>>> edit object attribute keys')
        # pprint.pprint(edit.__dict__.keys())
        fmt_str = ' {0:2d} | {1:>5} | {2:6d} | {3:8d} | {4:8d} | {5:8d} | {6:7d} | {7:6d} | {8:8d} | {9:5d} |'
        print(fmt_str.format(i, name, 
                             len(edit.things),  len(edit.vertexes), len(edit.linedefs), len(edit.sidedefs), 
                             len(edit.sectors), len(edit.segs),     len(edit.ssectors), len(edit.nodes)))
