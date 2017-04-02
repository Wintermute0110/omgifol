#!/usr/bin/python
# Original from Fredrik Johansson, 2006-12-11 
# Incorporates code by Frans P. de Vries, 2016-04-26 
# Incorporates code by Wintermute0110, 2017-03-11
#
# Image size table:
#   1080p -- 1920 x 1080
#    720p -- 1280 x  720
#    576p --  720 x  576
#    480p --  720 x  480
#
# Ideas for map drawing. This allows to have several maps per level for extrafanart
#   a) LINEDEFS: plot linedefs and change colour for two sided/action linedefs
#   b) SECTORS:  plot sectors (sectors with same height have same colour)
#   c) SSECTORS: plot ssegs and ssectors
#   d) TEXTURED: plot sector floor textures (same as automap in GLPrBoom+)
#   e) VERTEXES: plot linedef vertices in one color and node builder-added vertices in another
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
sys.path.insert(0, moduledir) 
from omg import *

# -------------------------------------------------------------------------------------------------
# Globals
# -------------------------------------------------------------------------------------------------
VERBOSE = True
BORDER_PIXELS = 50

# -------------------------------------------------------------------------------------------------
# Vars
# -------------------------------------------------------------------------------------------------
class BBox:
    def __init__(self, left, right, bottom, top):
        self.left   = left
        self.right  = right
        self.bottom = bottom
        self.top    = top

# Defines all variables necessary for a 2 dimensional linear transformation.
class MapTransformation:
    def __init__(self, left, right, bottom, top):
        self.left   = left
        self.right  = right
        self.bottom = bottom
        self.top    = top

# -------------------------------------------------------------------------------------------------
# Drawing utility functions
# -------------------------------------------------------------------------------------------------
def draw_things(edit, map_BBox, scale, draw):
    RADIUS = 4
    xmin = map_BBox.left
    ymin = map_BBox.bottom
    for thing in edit.things:
        # >> Flip coordinates of Y axis
        p1x =  ( thing.x - xmin) * scale + BORDER_PIXELS + xoffset
        p1y =  (-thing.y - ymin) * scale + BORDER_PIXELS + yoffset
        color = (0, 255, 0)
        draw.ellipse((p1x-RADIUS, p1y-RADIUS, p1x+RADIUS, p1y+RADIUS), outline = color)


# -------------------------------------------------------------------------------------------------
# Top level map drawing functions
# -------------------------------------------------------------------------------------------------
def drawmap_fit(wad, name, filename, format, pxsize, pysize):
    if VERBOSE:
        print('drawmap_fit() pxsize = {0}'.format(pxsize))
        print('drawmap_fit() pysize = {0}'.format(pysize))

    # --- Load map in editor ---
    edit = MapEditor(wad.maps[name])
    
    # --- Determine scale = map area unit / pixel ---
    xmin = min([v.x for v in edit.vertexes])
    xmax = max([v.x for v in edit.vertexes])
    ymin = min([v.y for v in edit.vertexes])
    ymax = max([v.y for v in edit.vertexes])
    map_BBox = BBox(xmin, xmax, ymin, ymax)
    xsize = map_BBox.right - map_BBox.left
    ysize = map_BBox.top - map_BBox.bottom
    scale_x = (pxsize-BORDER_PIXELS*2) / float(xsize)
    scale_y = (pysize-BORDER_PIXELS*2) / float(ysize)
    if scale_x < scale_y:
        scale = scale_x
        xoffset = 0
        # yoffset = (pysize - int(ysize*scale)) / 2
        yoffset = 0
    else:
        scale = scale_y
        # xoffset = (pxsize - int(xsize*scale)) / 2
        xoffset = 0
        yoffset = 0

    if VERBOSE:
        print('drawmap_fit() xmin  = {0}'.format(xmin))
        print('drawmap_fit() xmax  = {0}'.format(xmax))
        print('drawmap_fit() ymin  = {0}'.format(ymin))
        print('drawmap_fit() ymax  = {0}'.format(ymax))
        print('drawmap_fit() xsize = {0}'.format(xsize))
        print('drawmap_fit() ysize = {0}'.format(ysize))
        print('drawmap_fit() scale_x = {0}'.format(scale_x))
        print('drawmap_fit() scale_y = {0}'.format(scale_y))
        print('drawmap_fit() scale   = {0}'.format(scale))

    # --- Create image ---
    im = Image.new('RGB', (pxsize, pysize), (255, 255, 255))
    draw = ImageDraw.Draw(im)

    # --- Draw lines ---
    edit.linedefs.sort(lambda a, b: cmp(not a.two_sided, not b.two_sided))
    for line in edit.linedefs:
        # >> Flip coordinates of Y axis
        p1x = (edit.vertexes[line.vx_a].x + xmin) * scale + BORDER_PIXELS + xoffset
        p1y = (edit.vertexes[line.vx_a].y + ymin) * scale + BORDER_PIXELS + yoffset
        p2x = (edit.vertexes[line.vx_b].x + xmin) * scale + BORDER_PIXELS + xoffset
        p2y = (edit.vertexes[line.vx_b].y + ymin) * scale + BORDER_PIXELS + yoffset
        p1y = -p1y
        p2y = -p2y
        color = (0, 0, 0)
        if   line.two_sided: color = (144, 144, 144)
        elif line.action:    color = (220, 130, 50)

        # >> Draw several lines to simulate thickness 
        draw.line((p1x, p1y, p2x, p2y), fill = color)
        draw.line((p1x+1, p1y, p2x+1, p2y), fill = color)
        draw.line((p1x-1, p1y, p2x-1, p2y), fill = color)
        draw.line((p1x, p1y+1, p2x, p2y+1), fill = color)
        draw.line((p1x, p1y-1, p2x, p2y-1), fill = color)

    # --- Draw things ---
    # draw_things(edit, map_BBox, scale, draw)

    # --- Draw XY axis ---
    # NOTE ymin, ymax already inverted!!! This is a workaround
    pxmin = (xmin - xmin) * scale + BORDER_PIXELS + xoffset
    pxmax = (xmax - xmin) * scale + BORDER_PIXELS + xoffset
    pymin = (ymin - ymin) * scale + BORDER_PIXELS + yoffset
    pymax = (ymax - ymin) * scale + BORDER_PIXELS + yoffset
    pxzero = (0 - xmin) * scale + BORDER_PIXELS + xoffset
    pyzero = (0 - ymin) * scale + BORDER_PIXELS + yoffset
    color = (255, 0, 0)
    draw.line((pxmin, pyzero, pxmax, pyzero), fill = color)
    draw.line((pxzero, pymin, pxzero, pymax), fill = color)

    # --- Save image file ---
    del draw
    im.save(filename, format)

def drawmap_width(wad, name, filename, format, pxwidth):
    # Load map in editor
    edit = MapEditor(wad.maps[name])
    
    # Determine scale = map area unit / pixel
    xmin = min([v.x for v in edit.vertexes])
    xmax = max([v.x for v in edit.vertexes])
    ymin = min([-v.y for v in edit.vertexes])
    ymax = max([-v.y for v in edit.vertexes])
    xsize = xmax - xmin
    ysize = ymax - ymin
    scale = (pxwidth-BORDER_PIXELS*2) / float(max(xsize, ysize))
    if VERBOSE:
        print('drawmap_width() xmin  = {0}'.format(xmin))
        print('drawmap_width() xmax  = {0}'.format(xmax))
        print('drawmap_width() ymin  = {0}'.format(ymin))
        print('drawmap_width() ymax  = {0}'.format(ymax))
        print('drawmap_width() xsize = {0}'.format(xsize))
        print('drawmap_width() ysize = {0}'.format(ysize))
        print('drawmap_width() scale = {0}'.format(scale))

    # Convert all numbers to image space
    pxsize = int(xsize*scale) + BORDER_PIXELS*2;
    pysize = int(ysize*scale) + BORDER_PIXELS*2;
    if VERBOSE:
        print('drawmap_width() pxsize = {0}'.format(pxsize))
        print('drawmap_width() pysize = {0}'.format(pysize))

    # --- Create image ---
    im = Image.new('RGB', (pxsize, pysize), (255, 255, 255))
    draw = ImageDraw.Draw(im)

    # --- Draw lines ---
    edit.linedefs.sort(lambda a, b: cmp(not a.two_sided, not b.two_sided))
    for line in edit.linedefs:
        # >> Flip coordinates of Y axis
        p1x =  ( edit.vertexes[line.vx_a].x - xmin) * scale + BORDER_PIXELS
        p1y =  (-edit.vertexes[line.vx_a].y - ymin) * scale + BORDER_PIXELS
        p2x =  ( edit.vertexes[line.vx_b].x - xmin) * scale + BORDER_PIXELS
        p2y =  (-edit.vertexes[line.vx_b].y - ymin) * scale + BORDER_PIXELS
        color = (0, 0, 0)
        if   line.two_sided: color = (144, 144, 144)
        elif line.action:    color = (220, 130, 50)

        # >> Draw several lines to simulate thickness 
        draw.line((p1x, p1y, p2x, p2y), fill = color)
        draw.line((p1x+1, p1y, p2x+1, p2y), fill = color)
        draw.line((p1x-1, p1y, p2x-1, p2y), fill = color)
        draw.line((p1x, p1y+1, p2x, p2y+1), fill = color)
        draw.line((p1x, p1y-1, p2x, p2y-1), fill = color)

    # --- Draw things ---
    RADIUS = 5
    for thing in edit.things:
        # pprint.pprint(vars(thing))

        # >> Flip coordinates of Y axis
        p1x =  ( thing.x - xmin) * scale + BORDER_PIXELS
        p1y =  (-thing.y - ymin) * scale + BORDER_PIXELS

        # >> Change colour depending on flags
        color = (0, 255, 0)
        # if   thing.flags <= 2: color = (200,  0,   0)
        # elif thing.flags <= 4: color = (0,  100, 100)
        # elif thing.flags <= 8: color = (0,    0, 200)

        # >> Draw circle centered on thing
        draw.ellipse((p1x-RADIUS, p1y-RADIUS, p1x+RADIUS, p1y+RADIUS), outline = color)

    # --- Draw XY axis ---
    # NOTE ymin, ymax already inverted!!! This is a workaround
    pxmin = (xmin - xmin) * scale + BORDER_PIXELS
    pxmax = (xmax - xmin) * scale + BORDER_PIXELS
    pymin = (ymin - ymin) * scale + BORDER_PIXELS
    pymax = (ymax - ymin) * scale + BORDER_PIXELS
    pxzero = (0 - xmin) * scale + BORDER_PIXELS
    pyzero = (0 - ymin) * scale + BORDER_PIXELS
    color = (255, 0, 0)
    draw.line((pxmin, pyzero, pxmax, pyzero), fill = color)
    draw.line((pxzero, pymin, pxzero, pymax), fill = color)

    # --- Draw MAP bounding box ---
    # color = (0, 0, 255)
    # draw.line((pxmin, pymin, pxmin, pymax), fill = color) # left
    # draw.line((pxmin, pymin, pxmax, pymin), fill = color) # bottom
    # draw.line((pxmax, pymin, pxmax, pymax), fill = color) # right
    # draw.line((pxmin, pymax, pxmax, pymax), fill = color) # top

    # --- Draw grid ---
    # scale_size = 654 * scale
    # draw.line((10, 10, 10 + scale_size, 10), fill=(255, 0, 0))

    # --- Draw scale on top-left corner ---
    # A level must be contained within a 16384-unit radius as measured from its center point. 
    # A---------B---------C   big gap 327 map units
    # |         |         |   small gap 163 map units
    # |         E         |   
    # D                   F
    #
    A_px = (xmin - xmin) * scale + BORDER_PIXELS
    A_py = (ymax - ymin) * scale + BORDER_PIXELS
    B_px = (xmin + 163 - xmin) * scale + BORDER_PIXELS
    B_py = (ymax - ymin) * scale + BORDER_PIXELS
    C_px = (xmin + 327 - xmin) * scale + BORDER_PIXELS
    C_py = (ymax - ymin) * scale + BORDER_PIXELS
    D_px = (xmin - xmin) * scale + BORDER_PIXELS
    D_py = (ymax - 48 - ymin) * scale + BORDER_PIXELS
    F_px = (xmin + 327 - xmin) * scale + BORDER_PIXELS
    F_py = (ymax - 48 - ymin) * scale + BORDER_PIXELS

    color = (123, 104, 238)
    draw.line((A_px, A_py, B_px, B_py), fill = color) # A -> B
    draw.line((B_px, B_py, C_px, C_py), fill = color) # B -> C
    draw.line((A_px, A_py, D_px, D_py), fill = color) # A -> D
    draw.line((C_px, C_py, F_px, F_py), fill = color) # C -> F

    # --- Save image file ---
    del draw
    im.save(filename, format)

# -------------------------------------------------------------------------------------------------
# main ()
# -------------------------------------------------------------------------------------------------
if len(sys.argv) < 2:
    print('Omgifol DEMO script: draw maps to image files')
    print('Draw all maps whose names match the given pattern (eg E?M4 or MAP*)')
    print('to image files of a given format (PNG, BMP, etc). width specifies the')
    print('desired width of the output images.\n')
    print('Usage: drawmaps.py [options] source.wad\n')
    print('  -p pattern  Patterns may be "E?M?", "MAP01", "MAP*". Defaults to all level (pattern "*")')
    print('  -f format   May be PNG, BMP, JPEG. Defaults to PNG')
    print('  -w width    Width in pixels. Defaults to 1920 (for a 1920x1080 image)')
    print('  -s size     Fits map on given image size. size may be 1080p, 720p, 576p, 480p')
    print('  -things     Draws things on maps')
    print('  -axis       Draws cartesian axis on maps')
    print('  -scale      Draws a map scale on the upper right corner')

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
    elif o == '-f': format = a
    elif o == '-w': width = int(a)
    else:
        assert False, "Unhandled option"

# --- Load WAD ---
print('Loading WAD "{0}" ...'.format(wad_filename))
inwad = WAD()
inwad.from_file(wad_filename)
for name in inwad.maps.find(pattern):
    filename = os.path.splitext(wad_filename)[0] + '_' + name + '.' + format.lower()
    print('Drawing map {0} on file "{1}"'.format(name, filename))
    # drawmap_width(inwad, name, filename, format, width)
    drawmap_fit(inwad, name, filename, format, 1920, 1080)
sys.exit(0)
