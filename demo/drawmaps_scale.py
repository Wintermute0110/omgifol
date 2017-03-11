#!/usr/bin/python
# based on https://sourceforge.net/p/omgifol/code/HEAD/tree/demo/drawmaps.py
# original by Fredrik Johansson, 2006-12-11
# updated  by Frans P. de Vries, 2016-04-26

import sys, getopt
from omg import *
from PIL import Image, ImageDraw

verbose = False
border = 4
scales = 0
total = 0

def drawmap(wad, name, filename, maxpixels, reqscale):
    global verbose, scales, total
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

    if verbose:
        print "\t%0.2f: %d x %d" % (1.0/scale, xsize, ysize)
    im = Image.new('RGB', (xsize, ysize), (255,255,255))
    draw = ImageDraw.Draw(im)

    # draw 1s lines after 2s lines so 1s lines are never obscured
    edit.linedefs.sort(lambda a, b: cmp(not a.two_sided, not b.two_sided))

    for line in edit.linedefs:
         p1x = edit.vertexes[line.vx_a].x - xmin + border
         p1y = edit.vertexes[line.vx_a].y - ymin + border
         p2x = edit.vertexes[line.vx_b].x - xmin + border
         p2y = edit.vertexes[line.vx_b].y - ymin + border
         color = 0, 0, 0
         if line.two_sided: color = (144, 144, 144)
         if line.action: color = (220, 130, 50)

         # draw several lines to simulate thickness
         draw.line((p1x, p1y, p2x, p2y), fill=color)
         draw.line((p1x+1, p1y, p2x+1, p2y), fill=color)
         draw.line((p1x-1, p1y, p2x-1, p2y), fill=color)
         draw.line((p1x, p1y+1, p2x, p2y+1), fill=color)
         draw.line((p1x, p1y-1, p2x, p2y-1), fill=color)

    del draw
    im.save(filename)

if len(sys.argv) < 3:
    print "\n    Omgifol script: draw maps to image files\n"
    print "    Usage:"
    print "    drawmaps.py [-v] source.wad pattern [size [scale]]\n"
    print "    Draw all maps whose names match the given pattern (eg E?M4 or MAP*)"
    print "    If no 'size' is specified, default size is 1000 px"
    print "    With 'scale' specified, all maps are rendered at that same scale,"
    print "    but still capped to 'size' if needed"
    print "    With verbose flag '-v', log actual scale & dimensions per map and,"
    print "    without 'scale', also log the average scale for all maps\n"
else:
    # process optional verbose flag
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'v')
        for o, a in opts:
            if o == '-v':
                verbose = True
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)

    print "Loading %s..." % args[0]
    inwad = WAD()
    inwad.from_file(args[0])
    # collect optional limits
    try:
        maxpixels = int(args[2])
        try:
            reqscale = float(args[3])
        except:
            reqscale = 0
    except:
        maxpixels = 1000
        reqscale = 0

    for name in inwad.maps.find(args[1]):
        print "Drawing %s" % name
        drawmap(inwad, name, name + ".png", maxpixels, reqscale)

    if verbose and total > 1:
        print "\nAvg scale: %0.2f" % (1.0 / (scales / total))
