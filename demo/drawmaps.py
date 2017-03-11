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
# print('real_path  "{0}"'.format(real_path))
# print('currentdir "{0}"'.format(currentdir))
# print('parentdir  "{0}"'.format(parentdir))
# print('moduledir  "{0}"'.format(moduledir))
sys.path.insert(0, moduledir) 
from omg import *

# -------------------------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------------------------
def drawmap(wad, name, filename, width, format):
    xsize = width - 8

    edit = MapEditor(wad.maps[name])
    xmin = ymin = 32767
    xmax = ymax = -32768
    for v in edit.vertexes:
        xmin = min(xmin, v.x)
        xmax = max(xmax, v.x)
        ymin = min(ymin, -v.y)
        ymax = max(ymax, -v.y)

    scale = xsize / float(xmax - xmin)
    xmax = int(xmax * scale)
    xmin = int(xmin * scale)
    ymax = int(ymax * scale)
    ymin = int(ymin * scale)

    for v in edit.vertexes:
        v.x = v.x * scale
        v.y = -v.y * scale

    im = Image.new('RGB', ((xmax - xmin) + 8, (ymax - ymin) + 8), (255,255,255))
    draw = ImageDraw.Draw(im)

    edit.linedefs.sort(lambda a, b: cmp(not a.two_sided, not b.two_sided))

    for line in edit.linedefs:
         p1x = edit.vertexes[line.vx_a].x - xmin + 4
         p1y = edit.vertexes[line.vx_a].y - ymin + 4
         p2x = edit.vertexes[line.vx_b].x - xmin + 4
         p2y = edit.vertexes[line.vx_b].y - ymin + 4

         color = (0, 0, 0)
         if line.two_sided:
             color = (144, 144, 144)
         if line.action:
             color = (220, 130, 50)

         draw.line((p1x, p1y, p2x, p2y), fill=color)
         # draw.line((p1x+1, p1y, p2x+1, p2y), fill=color)
         # draw.line((p1x-1, p1y, p2x-1, p2y), fill=color)
         # draw.line((p1x, p1y+1, p2x, p2y+1), fill=color)
         # draw.line((p1x, p1y-1, p2x, p2y-1), fill=color)

    # --- Draw scale (or grid or XY axis) ---
    scale_size = 654 * scale
    draw.line((10, 10, 10 + scale_size, 10), fill=(255, 0, 0))

    del draw

    im.save(filename, format)

# -------------------------------------------------------------------------------------------------
# main ()
# -------------------------------------------------------------------------------------------------
if len(sys.argv) < 5:
    print('Omgifol script: draw maps to image files')
    print('Draw all maps whose names match the given pattern (eg E?M4 or MAP*) '
          'to image files of a given format (PNG, BMP, etc). width specifies the '
          'desired width of the output images.\n')
    print('Usage: drawmaps.py source.wad [pattern [width [format]]]')
    print('pattern examples: "E?M?", "MAP01", "MAP*" or all')
    print('width is in pixels')
    print('format may be PNG, BMP, JPEG. Defaults to JPEG')
else:
    print('Loading WAD "{0}" ...'.format(sys.argv[1]))
    inwad = WAD()
    inwad.from_file(sys.argv[1])
    width = int(sys.argv[3])
    format = sys.argv[4].upper()
    for name in inwad.maps.find(sys.argv[2]):
        filename = os.path.splitext(sys.argv[1])[0] + '_' + name + '.' + format.lower()
        print('Drawing map {0} on file "{1}"'.format(name, filename))
        drawmap(inwad, name, filename, width, format)
