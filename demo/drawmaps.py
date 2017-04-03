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
# Ideas for map drawing. This allows to have several maps per level for extrafanart.
#   a) LINEDEFS: plot linedefs and change colour for two sided/action linedefs
#   b) SECTORS:  plot sectors (sectors with same height have same colour)
#   c) NODES:    plot ssegs and ssectors
#   d) VERTEXES: plot linedef vertices in one color and node-builder-added vertices in another
#
# For the future:
#   a) TEXTURED: plot sector floor textures (same as automap in GLPrBoom+)
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
BORDER_PIXELS = 0

MAP_LINEDEFS = 100
MAP_SECTORS  = 200
MAP_NODES    = 300
MAP_VERTEXES = 400

# -------------------------------------------------------------------------------------------------
# Vars
# -------------------------------------------------------------------------------------------------
class BBox:
    def __init__(self, left, right, bottom, top):
        self.left   = left
        self.right  = right
        self.bottom = bottom
        self.top    = top
        self.xsize  = right - left
        self.ysize  = top - bottom

# See https://github.com/chocolate-doom/chocolate-doom/blob/sdl2-branch/src/doom/am_map.c
class ColorScheme:
    def __init__(self, back, wall, tswall, fdwall, cdwall, awall, thing):
        self.BG     = back
        self.WALL   = wall   # One sided linedef
        self.TSWALL = tswall # Two sided linedef
        self.FDWALL = fdwall # Two sided, floor level change
        self.CDWALL = cdwall # Two sided, ceiling level change and same floor level
        self.AWALL  = awall  # Action wall
        self.THING  = thing  # Thing color

CDoomWorld = ColorScheme(
    (255, 255, 255),
    (0, 0, 0),
    (144, 144, 144),
    (0, 255, 0),
    (0, 0, 255),
    (220, 130, 50),
    (0, 255, 0)
)

CClassic = ColorScheme(
    (0, 0, 0),
    (255, 0, 0),
    (144, 144, 144),
    (0, 255, 0),
    (0, 0, 255),
    (220, 130, 50),
    (0, 255, 0)
)

# -------------------------------------------------------------------------------------------------
# Drawing utility functions
# -------------------------------------------------------------------------------------------------
def draw_line(draw, p1x, p1y, p2x, p2y, color):
    draw.line((p1x, p1y, p2x, p2y), fill = color)

def draw_thick_line(draw, p1x, p1y, p2x, p2y, color):
    draw.line((p1x, p1y, p2x, p2y), fill = color)
    draw.line((p1x+1, p1y, p2x+1, p2y), fill = color)
    draw.line((p1x-1, p1y, p2x-1, p2y), fill = color)
    draw.line((p1x, p1y+1, p2x, p2y+1), fill = color)
    draw.line((p1x, p1y-1, p2x, p2y-1), fill = color)

#
# In the future draw a triangle like Vanilla Doom
#
RADIUS = 4
def draw_thing(draw, p1x, p1y, angle, color):
    draw.ellipse((p1x-RADIUS, p1y-RADIUS, p1x+RADIUS, p1y+RADIUS), outline = color)

# -------------------------------------------------------------------------------------------------
# Top level map drawing functions
# -------------------------------------------------------------------------------------------------
def drawmap_fit(wad, map_name, filename, format, map_type, pxsize, pysize, cscheme):
    pxsize_noborder = pxsize - BORDER_PIXELS*2
    pysize_noborder = pysize - BORDER_PIXELS*2
    if VERBOSE:
        print('drawmap_fit() pxsize          = {0}'.format(pxsize))
        print('drawmap_fit() pysize          = {0}'.format(pysize))
        print('drawmap_fit() pxsize_noborder = {0}'.format(pxsize_noborder))
        print('drawmap_fit() pysize_noborder = {0}'.format(pysize_noborder))

    # --- Load map in editor ---
    edit = MapEditor(wad.maps[map_name])

    # --- Determine scale = map area unit / pixel ---
    xmin = min([v.x for v in edit.vertexes])
    xmax = max([v.x for v in edit.vertexes])
    ymin = min([v.y for v in edit.vertexes])
    ymax = max([v.y for v in edit.vertexes])
    mapBBox = BBox(xmin, xmax, ymin, ymax)
    xscale = pxsize_noborder / float(mapBBox.xsize)
    yscale = pysize_noborder / float(mapBBox.ysize)
    if VERBOSE:
        print('drawmap_fit() xmin   = {0}'.format(mapBBox.left))
        print('drawmap_fit() xmax   = {0}'.format(mapBBox.right))
        print('drawmap_fit() ymin   = {0}'.format(mapBBox.bottom))
        print('drawmap_fit() ymax   = {0}'.format(mapBBox.top))
        print('drawmap_fit() xsize  = {0}'.format(mapBBox.xsize))
        print('drawmap_fit() ysize  = {0}'.format(mapBBox.ysize))
        print('drawmap_fit() xscale = {0}'.format(xscale))
        print('drawmap_fit() yscale = {0}'.format(yscale))

    if xscale < yscale:
        scale = xscale
        xoffset = 0
        yoffset = (pysize - int(mapBBox.ysize*scale)) / 2
    else:
        scale = yscale
        xoffset = (pxsize - int(mapBBox.xsize*scale)) / 2
        yoffset = 0

    if VERBOSE:
        print('drawmap_fit() scale   = {0}'.format(scale))
        print('drawmap_fit() xoffset = {0}'.format(xoffset))
        print('drawmap_fit() yoffset = {0}'.format(yoffset))

    # --- Create image ---
    im = Image.new('RGB', (pxsize, pysize), cscheme.BG)
    draw = ImageDraw.Draw(im)

    if map_type == MAP_LINEDEFS:
        # --- Draw lines ---
        edit.linedefs.sort(lambda a, b: cmp(not a.two_sided, not b.two_sided))
        for line in edit.linedefs:
            p1x = scale * (edit.vertexes[line.vx_a].x - mapBBox.left)   + xoffset
            p1y = scale * (edit.vertexes[line.vx_a].y - mapBBox.bottom) + yoffset
            p2x = scale * (edit.vertexes[line.vx_b].x - mapBBox.left)   + xoffset
            p2y = scale * (edit.vertexes[line.vx_b].y - mapBBox.bottom) + yoffset
            # print('{0} {1} --> {2} {3}'.format(p1x, p1y, p2x, p2y))

            color = cscheme.WALL
            if   line.two_sided: color = cscheme.TSWALL
            elif line.action:    color = cscheme.AWALL

            # >> Draw several lines to simulate thickness
            # draw_line(draw, p1x, p1y, p2x, p2y, color)
            draw_thick_line(draw, p1x, p1y, p2x, p2y, color)

        # --- Draw things ---
        # for thing in edit.things:
        #     p1x = scale *(thing.x - mapBBox.left) + xoffset
        #     p1y = scale *(thing.y - mapBBox.bottom) + yoffset
        #     draw_thing(draw, p1x, p1y, thing.angle, cscheme.THING)

    elif map_type == MAP_VERTEXES:
        # --- Draw lines ---
        edit.linedefs.sort(lambda a, b: cmp(not a.two_sided, not b.two_sided))
        for line in edit.linedefs:
            p1x = scale * (edit.vertexes[line.vx_a].x - mapBBox.left)   + xoffset
            p1y = scale * (edit.vertexes[line.vx_a].y - mapBBox.bottom) + yoffset
            p2x = scale * (edit.vertexes[line.vx_b].x - mapBBox.left)   + xoffset
            p2y = scale * (edit.vertexes[line.vx_b].y - mapBBox.bottom) + yoffset
            color = cscheme.WALL
            draw_line(draw, p1x, p1y, p2x, p2y, color)

        # --- Plot vertices not belonging to a linedef ---
        SIZE = 2
        linedefs_vertexes = set()
        for line in edit.linedefs:
            linedefs_vertexes.add(line.vx_a)
            linedefs_vertexes.add(line.vx_b)
        for v_index in range(len(edit.vertexes)):
            # print(vars(vertex))
            color = (0, 255, 255)
            if v_index not in linedefs_vertexes: color = (255, 255, 0)
            p1x = scale *(edit.vertexes[v_index].x - mapBBox.left) + xoffset
            p1y = scale *(edit.vertexes[v_index].y - mapBBox.bottom) + yoffset
            draw.point((p1x, p1y), fill = color)
            draw.rectangle((p1x-SIZE, p1y-SIZE, p1x+SIZE, p1y+SIZE), fill = color)

    elif map_type == MAP_SECTORS:
        # --- Draw linedefs ---
        for line in edit.linedefs:
            p1x = scale * (edit.vertexes[line.vx_a].x - mapBBox.left)   + xoffset
            p1y = scale * (edit.vertexes[line.vx_a].y - mapBBox.bottom) + yoffset
            p2x = scale * (edit.vertexes[line.vx_b].x - mapBBox.left)   + xoffset
            p2y = scale * (edit.vertexes[line.vx_b].y - mapBBox.bottom) + yoffset
            color = cscheme.WALL
            draw_line(draw, p1x, p1y, p2x, p2y, color)

    elif map_type == MAP_NODES:
        # --- Draw segs and ssectors ---
        # http://doom.wikia.com/wiki/Subsector
        # http://doom.wikia.com/wiki/User_talk:Fraggle#Making_polygons
        # https://www.doomworld.com/vb/doom-editing/43976-subsector-viewer/
        # https://www.doomworld.com/vb/doom-general/70565-quesiton-about-the-nodes-lump-and-subsectors/
        #
        print('{0} segs'.format(len(edit.segs)))
        print('{0} linedefs'.format(len(edit.linedefs)))

        # --- Draw linedefs ---
        for line in edit.linedefs:
            p1x = scale * (edit.vertexes[line.vx_a].x - mapBBox.left)   + xoffset
            p1y = scale * (edit.vertexes[line.vx_a].y - mapBBox.bottom) + yoffset
            p2x = scale * (edit.vertexes[line.vx_b].x - mapBBox.left)   + xoffset
            p2y = scale * (edit.vertexes[line.vx_b].y - mapBBox.bottom) + yoffset
            color = cscheme.WALL
            draw_line(draw, p1x, p1y, p2x, p2y, color)

        # --- Draw segs ---
        for seg in edit.segs:
            line = edit.linedefs[seg.line]
            # print(vars(seg))
            # print(vars(line))
            
            seg_vx_a  = seg.vx_a
            seg_vx_b  = seg.vx_b
            line_vx_a = line.vx_a
            line_vx_b = line.vx_b

            if seg_vx_a != line_vx_a or seg_vx_b != line_vx_b:
                print('seg_vx_a  {0:5d}   seg_vx_b {1:5d}'.format(seg_vx_a, seg_vx_b))
                print('line_vx_a {0:5d}  line_vx_b {1:5d}'.format(line_vx_a, line_vx_b))

                p1x = scale * (edit.vertexes[seg.vx_a].x - mapBBox.left)   + xoffset
                p1y = scale * (edit.vertexes[seg.vx_a].y - mapBBox.bottom) + yoffset
                p2x = scale * (edit.vertexes[seg.vx_b].x - mapBBox.left)   + xoffset
                p2y = scale * (edit.vertexes[seg.vx_b].y - mapBBox.bottom) + yoffset
                color = cscheme.FDWALL
                draw_line(draw, p1x, p1y, p2x, p2y, color)

        # --- Plot vertices not belonging to a linedef ---
        SIZE = 2
        linedefs_vertexes = set()
        for line in edit.linedefs:
            linedefs_vertexes.add(line.vx_a)
            linedefs_vertexes.add(line.vx_b)
        for v_index in range(len(edit.vertexes)):
            # print(vars(vertex))
            color = (0, 255, 255)
            if v_index not in linedefs_vertexes: color = (255, 255, 0)
            p1x = scale *(edit.vertexes[v_index].x - mapBBox.left) + xoffset
            p1y = scale *(edit.vertexes[v_index].y - mapBBox.bottom) + yoffset
            draw.point((p1x, p1y), fill = color)
            draw.rectangle((p1x-SIZE, p1y-SIZE, p1x+SIZE, p1y+SIZE), fill = color)

    # --- Draw XY axis ---
    # NOTE ymin, ymax already inverted!!! This is a workaround
    # pxmin = (xmin - xmin) * scale + BORDER_PIXELS + xoffset
    # pxmax = (xmax - xmin) * scale + BORDER_PIXELS + xoffset
    # pymin = (ymin - ymin) * scale + BORDER_PIXELS + yoffset
    # pymax = (ymax - ymin) * scale + BORDER_PIXELS + yoffset
    # pxzero = (0 - xmin) * scale + BORDER_PIXELS + xoffset
    # pyzero = (0 - ymin) * scale + BORDER_PIXELS + yoffset
    # color = (255, 0, 0)
    # draw.line((pxmin, pyzero, pxmax, pyzero), fill = color)
    # draw.line((pxzero, pymin, pxzero, pymax), fill = color)

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
    fn_prefix = os.path.splitext(wad_filename)[0] + '_' + name
    fn_sufix  = '.' + format.lower()
    print('Drawing map {0} on file "{1}"'.format(name, fn_prefix))
    # drawmap_width(inwad, name, filename, format, width)
    # drawmap_fit(inwad, name, fn_prefix + '_Line_A' + fn_sufix, format, MAP_LINEDEFS, 1920, 1080, CDoomWorld)
    # drawmap_fit(inwad, name, fn_prefix + '_Line_B' + fn_sufix, format, MAP_LINEDEFS, 1920, 1080, CClassic)
    # drawmap_fit(inwad, name, fn_prefix + '_Ver_A' + fn_sufix, format, MAP_VERTEXES, 1920, 1080, CDoomWorld)
    # drawmap_fit(inwad, name, fn_prefix + '_Ver_B' + fn_sufix, format, MAP_VERTEXES, 1920, 1080, CClassic)
    # drawmap_fit(inwad, name, fn_prefix + '_Sec_A' + fn_sufix, format, MAP_SECTORS, 1920, 1080, CDoomWorld)
    # drawmap_fit(inwad, name, fn_prefix + '_Sec_B' + fn_sufix, format, MAP_SECTORS, 1920, 1080, CClassic)
    drawmap_fit(inwad, name, fn_prefix + '_Nodes_A' + fn_sufix, format, MAP_NODES, 1920, 1080, CDoomWorld)
    drawmap_fit(inwad, name, fn_prefix + '_Nodes_B' + fn_sufix, format, MAP_NODES, 1920, 1080, CClassic)

sys.exit(0)
