#!/usr/bin/python
# Original from Fredrik Johansson, 2006-12-11 
# Incorporates code by Frans P. de Vries, 2016-04-26 
# Incorporates code by Wintermute0110, 2017-03-11
#
#  720p -- 1280x720
# 1080p -- 1920x1080
#
import sys
import os
import getopt
import pprint
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
# Globals
# -------------------------------------------------------------------------------------------------
global_verbose = True
border = 25
scales = 0
total = 0

# -------------------------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------------------------
def drawmap(wad, name, filename, width, format):
    global scales, total
    maxpixels = width
    reqscale = 0
    edit = MapEditor(wad.maps[name])
    
   # determine scale = map area unit / pixel
    xmin = min([v.x for v in edit.vertexes])
    xmax = max([v.x for v in edit.vertexes])
    ymin = min([-v.y for v in edit.vertexes])
    ymax = max([-v.y for v in edit.vertexes])
    xsize = xmax - xmin
    ysize = ymax - ymin
    scale = (maxpixels-border*2) / float(max(xsize, ysize))

    # tally for average scale or compare against requested scale
    if reqscale == 0:
        scales = scales + scale
        total = total + 1
    else:
        if scale > 1.0 / reqscale:
            scale = 1.0 / reqscale

    # convert all numbers to image space
    xmax = int(xmax*scale); xmin = int(xmin*scale)
    ymax = int(ymax*scale); ymin = int(ymin*scale)
    xsize = int(xsize*scale) + border*2;
    ysize = int(ysize*scale) + border*2;
    for v in edit.vertexes:
        v.x = v.x * scale; v.y = -v.y * scale 

    # --- Create image ---
    if global_verbose:
        print('drawmap() xsize = {0}'.format(xsize))
        print('drawmap() ysize = {0}'.format(ysize))
    im = Image.new('RGB', (xsize, ysize), (255,255,255))
    draw = ImageDraw.Draw(im)

    edit.linedefs.sort(lambda a, b: cmp(not a.two_sided, not b.two_sided))

    for line in edit.linedefs:
         p1x = edit.vertexes[line.vx_a].x - xmin + border
         p1y = edit.vertexes[line.vx_a].y - ymin + border
         p2x = edit.vertexes[line.vx_b].x - xmin + border
         p2y = edit.vertexes[line.vx_b].y - ymin + border
         color = (0, 0, 0)
         if line.two_sided: color = (144, 144, 144)
         if line.action:    color = (220, 130, 50)

         # draw several lines to simulate thickness 
         draw.line((p1x, p1y, p2x, p2y), fill=color)
         draw.line((p1x+1, p1y, p2x+1, p2y), fill=color)
         draw.line((p1x-1, p1y, p2x-1, p2y), fill=color)
         draw.line((p1x, p1y+1, p2x, p2y+1), fill=color)
         draw.line((p1x, p1y-1, p2x, p2y-1), fill=color)

    # --- Draw scale (or grid or XY axis) ---
    # scale_size = 654 * scale
    # draw.line((10, 10, 10 + scale_size, 10), fill=(255, 255, 0))

    # --- Draw XY axis ---
    # scale_size = 654 * scale
    # draw.line((10, 10, 10 + scale_size, 10), fill=(255, 0, 0))

    # --- Save image file ---
    del draw
    im.save(filename, format)

# -------------------------------------------------------------------------------------------------
# main ()
# -------------------------------------------------------------------------------------------------
if len(sys.argv) < 2:
    print('Omgifol script: draw maps to image files')
    print('Draw all maps whose names match the given pattern (eg E?M4 or MAP*)')
    print('to image files of a given format (PNG, BMP, etc). width specifies the')
    print('desired width of the output images.\n')
    print('Usage: drawmaps.py [-p pattern] [-w width [-f format] source.wad')
    print('  -p pattern  Patterns may be "E?M?", "MAP01", "MAP*"')
    print('              Defaults to all level (pattern "*")')
    print('  -w width    Width in pixels. Defaults to 1920 (for a 1920x1080 image)')
    print('  -f format   May be PNG, BMP, JPEG. Defaults to PNG')
    sys.exit(1)

# --- Parse arguments ---
opts, args = getopt.getopt(sys.argv[1:], 'p:w:f:')
pprint.pprint(opts)
pprint.pprint(args)
wad_filename = args[0]
pattern = '*'
width = 1920
format = 'PNG'
for o, a in opts:
    if   o == '-p': pattern = a
    elif o == '-w': width = int(a)
    elif o == '-f': format = a
    else:
        assert False, "Unhandled option"

# --- Load WAD ---
print('Loading WAD "{0}" ...'.format(wad_filename))
inwad = WAD()
inwad.from_file(wad_filename)
for name in inwad.maps.find(pattern):
    filename = os.path.splitext(wad_filename)[0] + '_' + name + '.' + format.lower()
    print('Drawing map {0} on file "{1}"'.format(name, filename))
    drawmap(inwad, name, filename, width, format)
sys.exit(0)
