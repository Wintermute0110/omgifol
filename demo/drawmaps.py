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
BORDER_PERCENT = 5

MAP_LINEDEFS = 100
MAP_SECTORS  = 200
MAP_NODES    = 300
MAP_VERTEXES = 400

# -------------------------------------------------------------------------------------------------
# Vars
# -------------------------------------------------------------------------------------------------
class LinearTransform:
    def __init__(self, left, right, bottom, top, px_size, py_size, border):
        self.left   = left
        self.right  = right
        self.bottom = bottom
        self.top    = top
        self.x_size  = right - left
        self.y_size  = top - bottom
        # --- Shift map in x or y direction ---
        self.pan_x  = 0
        self.pan_y  = 0

        print('LinearTransform() left       = {0}'.format(left))
        print('LinearTransform() right      = {0}'.format(right))
        print('LinearTransform() bottom     = {0}'.format(bottom))
        print('LinearTransform() top        = {0}'.format(top))
        print('LinearTransform() x_size     = {0}'.format(self.x_size))
        print('LinearTransform() y_size     = {0}'.format(self.y_size))

        # --- Calculate scale in [pixels] / [map_unit] ---
        self.px_size = px_size
        self.py_size = py_size
        self.border  = border
        self.border_x = px_size * border / 100
        self.border_y = py_size * border / 100
        self.pxsize_nob = px_size - 2*self.border_x
        self.pysize_nob = py_size - 2*self.border_y
        self.x_scale = self.pxsize_nob / float(self.x_size)
        self.y_scale = self.pysize_nob / float(self.y_size)
        if self.x_scale < self.y_scale:
            self.scale   = self.x_scale
            self.xoffset = self.border_x
            self.yoffset = (py_size - int(self.y_size*self.scale)) / 2
        else:
            self.scale   = self.y_scale
            self.xoffset = (px_size - int(self.x_size*self.scale)) / 2
            self.yoffset = self.border_y
        print('LinearTransform() px_size    = {0}'.format(px_size))
        print('LinearTransform() py_size    = {0}'.format(py_size))
        print('LinearTransform() border     = {0}'.format(border))
        print('LinearTransform() border_x   = {0}'.format(self.border_x))
        print('LinearTransform() border_y   = {0}'.format(self.border_y))
        print('LinearTransform() pxsize_nob = {0}'.format(self.pxsize_nob))
        print('LinearTransform() pysize_nob = {0}'.format(self.pysize_nob))
        print('LinearTransform() xscale     = {0}'.format(self.x_scale))
        print('LinearTransform() yscale     = {0}'.format(self.y_scale))
        print('LinearTransform() scale      = {0}'.format(self.scale))
        print('LinearTransform() xoffset    = {0}'.format(self.xoffset))
        print('LinearTransform() yoffset    = {0}'.format(self.yoffset))

    def MapToScreen(self, map_x, map_y):
        screen_x = self.scale * (+map_x - self.left) + self.xoffset
        screen_y = self.scale * (-map_y + self.top)  + self.yoffset

        return (screen_x, screen_y)

    def ScreenToMap(self, screen_x, screen_y):
        map_x = +(screen_x - self.xoffset + self.scale * self.left) / self.scale
        map_y = -(screen_y - self.yoffset - self.scale * self.top) / self.scale

        return (map_x, map_y)

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

def draw_axis(draw, LT, color):
    (pxzero, pyzero) = LT.MapToScreen(0, 0)
    draw.line((0, pyzero, LT.px_size, pyzero), fill = color)
    draw.line((pxzero, 0, pxzero, LT.py_size), fill = color)

#
# A level must be contained within a 16384-unit radius as measured from its center point.
# Point A is the top-left corner.
#
# A---------B---------C   A-C gap 327 map units
# |         |         |   A-B gap 163 map units
# |         E         |   A-D gap is 163/2 map units
# D                   F   B-E gap is 163/4 map units
#
def draw_scale(draw, LT, color):
    (A_px, A_py) = LT.MapToScreen(LT.left, LT.top)
    (B_px, B_py) = LT.MapToScreen(LT.left+163, LT.top)
    (C_px, C_py) = LT.MapToScreen(LT.left+327, LT.top)
    (D_px, D_py) = LT.MapToScreen(LT.left, LT.top-163/2)
    (E_px, E_py) = LT.MapToScreen(LT.left+163, LT.top-163/4)
    (F_px, F_py) = LT.MapToScreen(LT.left+327, LT.top-163/2)

    draw.line((A_px, A_py, C_px, C_py), fill = color) # A -> C
    draw.line((A_px, A_py, D_px, D_py), fill = color) # A -> D
    draw.line((B_px, B_py, E_px, E_py), fill = color) # B -> E
    draw.line((C_px, C_py, F_px, F_py), fill = color) # C -> F

#
# In the future draw a triangle like Vanilla Doom
# https://github.com/chocolate-doom/chocolate-doom/blob/sdl2-branch/src/doom/am_map.c#L186
# https://github.com/chocolate-doom/chocolate-doom/blob/sdl2-branch/src/doom/am_map.c#L1314
RADIUS = 4
def draw_thing(draw, map_x, map_y, angle, color):
    draw.ellipse((p1x-RADIUS, p1y-RADIUS, p1x+RADIUS, p1y+RADIUS), outline = color)

# -------------------------------------------------------------------------------------------------
# Top level map drawing functions
# -------------------------------------------------------------------------------------------------
def drawmap_fit(wad, map_name, filename, format, map_type, px_size, py_size, cscheme):
    # --- Load map in editor ---
    edit = MapEditor(wad.maps[map_name])

    # --- Determine scale = pixel / map unit ---
    xmin = min([v.x for v in edit.vertexes])
    xmax = max([v.x for v in edit.vertexes])
    ymin = min([v.y for v in edit.vertexes])
    ymax = max([v.y for v in edit.vertexes])
    LT = LinearTransform(xmin, xmax, ymin, ymax, px_size, py_size, BORDER_PERCENT)

    # --- Create image ---
    im = Image.new('RGB', (px_size, py_size), cscheme.BG)
    draw = ImageDraw.Draw(im)

    # --- Draw XY axis ---
    draw_axis(draw, LT, (200, 200, 200))

    # --- Draw map scale ---
    draw_scale(draw, LT, (150, 150, 150))

    # --- Draw map ---
    if map_type == MAP_LINEDEFS:
        # --- Draw lines ---
        edit.linedefs.sort(lambda a, b: cmp(not a.two_sided, not b.two_sided))
        for line in edit.linedefs:
            (p1x, p1y) = LT.MapToScreen(edit.vertexes[line.vx_a].x, edit.vertexes[line.vx_a].y)
            (p2x, p2y) = LT.MapToScreen(edit.vertexes[line.vx_b].x, edit.vertexes[line.vx_b].y)

            color = cscheme.WALL
            if   line.two_sided: color = cscheme.TSWALL
            elif line.action:    color = cscheme.AWALL

            # >> Draw several lines to simulate thickness
            # draw_line(draw, p1x, p1y, p2x, p2y, color)
            draw_thick_line(draw, p1x, p1y, p2x, p2y, color)

        # --- Draw things ---
        for thing in edit.things:
            # In the future use this function
            # draw_thing(draw, p1x, p1y, thing.angle, cscheme.THING)
            color = (0, 255, 0)
            (px, py) = LT.MapToScreen(thing.x, thing.y)
            draw.ellipse((px-RADIUS, py-RADIUS, px+RADIUS, py+RADIUS), outline = color)

    elif map_type == MAP_VERTEXES:
        # --- Draw lines ---
        edit.linedefs.sort(lambda a, b: cmp(not a.two_sided, not b.two_sided))
        for line in edit.linedefs:
            (p1x, p1y) = LT.MapToScreen(edit.vertexes[line.vx_a].x, edit.vertexes[line.vx_a].y)
            (p2x, p2y) = LT.MapToScreen(edit.vertexes[line.vx_b].x, edit.vertexes[line.vx_b].y)
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
            (p1x, p1y) = LT.MapToScreen(edit.vertexes[v_index].x, edit.vertexes[v_index].y)
            draw.rectangle((p1x-SIZE, p1y-SIZE, p1x+SIZE, p1y+SIZE), fill = color)

    elif map_type == MAP_SECTORS:
        # In the future draw the floor textures of each sector, like the map in PrBoom+ when using
        # OpenGL renderer.
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
        # Segs are only defined on linedefs and have implicit edges. I don't know how to
        # plot the implicit edges.
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
    # drawmap_fit(inwad, name, fn_prefix + '_Line_A' + fn_sufix, format, MAP_LINEDEFS, 1920, 1080, CDoomWorld)
    drawmap_fit(inwad, name, fn_prefix + '_Line_B' + fn_sufix, format, MAP_LINEDEFS, 1920, 1080, CClassic)
    # drawmap_fit(inwad, name, fn_prefix + '_Ver_A' + fn_sufix, format, MAP_VERTEXES, 1920, 1080, CDoomWorld)
    drawmap_fit(inwad, name, fn_prefix + '_Ver_B' + fn_sufix, format, MAP_VERTEXES, 1920, 1080, CClassic)
    # drawmap_fit(inwad, name, fn_prefix + '_Sec_A' + fn_sufix, format, MAP_SECTORS, 1920, 1080, CDoomWorld)
    # drawmap_fit(inwad, name, fn_prefix + '_Sec_B' + fn_sufix, format, MAP_SECTORS, 1920, 1080, CClassic)
    # drawmap_fit(inwad, name, fn_prefix + '_Nodes_A' + fn_sufix, format, MAP_NODES, 1920, 1080, CDoomWorld)
    # drawmap_fit(inwad, name, fn_prefix + '_Nodes_B' + fn_sufix, format, MAP_NODES, 1920, 1080, CClassic)

sys.exit(0)
