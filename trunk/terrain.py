#!/usr/bin/env python
"""Diamond-square random terrain generator

Usage examples:

Default Mountainous:
python terrain.py

High Desert:
python terrain.py --tree-line=0.1 --snow-line=10 --sand-line=100

Marsh:
python terrain.py --deviation=2 --water-line=2 --tree-line=6 --snow-line=100 --sand-line=100

Transitional:
python terrain.py --tree-line=4 --sand-line=-5 --water-line=-20 --smoothing=5 --iterations=8

Patchy Snow:
python terrain.py --deviation=2 --tree-line=6 --snow-line=2.5 --sand-line=2.4 --iterations=8

Jagged Wasteland:
python terrain.py --deviation=10 --smooth=2.0 --snow-line=100 --tree-line=-25 --sand-line=10

If you come up with any other interesting examples, please mail them to me!

And now a brief word from the lawyers:

Copyright (c) 2008 Casey Duncan (casey dot duncan at gmail.com)

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

  * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
  * Redistributions in binary form must reproduce the above copyright 
    notice, this list of conditions and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.
  * Neither the name of pyglet nor the names of its
    contributors may be used to endorse or promote products
    derived from this software without specific prior written
    permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

from math import sqrt, atan2, degrees
import random
import array
import itertools
import optparse
import pyglet
import ctypes
from pyglet.gl import *
from pyglet import window, font, clock # for pyglet 1.0
from pyglet.window import key
from airfoil import Airfoil
from euclid import *

class FractalTerrainMesh:

        def __init__(self, iterations, deviation, smooth, start=0.0,
                tree_line=12.0, water_line=0.0, snow_line=12.5, sand_line=1.5,
                display_width=100, seed=None, edge_smooth=1000.0, seamless=False):
                """
                Generate a random terrain mesh

                iterations -- Controls the detail of the mesh, and the cost to compute
                and draw it. Each iteration quadruples the number of vertices. Adding more 
                vertices also tends to make the terrain smoother. The number of iterations
                you need will depend on the display width of the terrain and how close
                up you view it.

                deviation -- Controls the overall vertical deviation from lowest
                to highest across the map. Higher deviations create mountainous terrain
                with high peaks and low valleys. High values also tend to make the terrain 
                more jagged.

                start -- Starting mean altitude, used to compute the elevations of the
                far corners of the terrain.

                smooth -- Controls how much the deviation is reduced each iteration,
                thereby controlling how much vertices deviate from the plane of
                their neighbors. Higher values result in smoother, more weathered 
                looking terrain.

                edge_smooth -- Divides deviation by this value along the terrain edge to
                avoid ragged artifacts.

                display_width -- The width of the terrain when displayed in arbitrary
                opengl units. Use this to scale the terrain accordingly with your scene.
                Larger display widths may require more iterations to look good.

                seed -- Random seed used to create the terrain. Due to the fractal algorithm,
                The same seed will generate the same basic terrain topology regardless of the
                number of iterations. This allows you to generate multiple equivilant
                terrain meshes with different levels of mesh detail or different aesthetic
                settings.

                seamless -- If true ensure the edges match so the terrain can be tiled.
                The current implementation of this is poor, feel free to improve it 8^)
                """
                self.display_width = display_width
                self.display_list = None
                smooth_step = (smooth - 1.0) / iterations
                self.water_line = water_line
                self.tree_line = tree_line
                self.sand_line = sand_line
                self.snow_line = snow_line

                # Generate vertices
                
                width = self.size = 2**iterations + 1                
                vertcount = width**2
                vert = self.vert = [array.array('f', itertools.repeat(0.0, width))
                        for i in range(width)]               
                random.seed(seed)
                vert[0][0] = random.gauss(start, deviation)
                vert[0][-1] = random.gauss(start, deviation)
                vert[-1][0] = random.gauss(start, deviation)
                vert[-1][-1] = random.gauss(start, deviation)
                span = width
                right = width - 1
                for i in range(iterations):
                        span /= 2
                        span2 = span * 2
                        r = range(2**i)
                        # Diamond pass
                        for x in r:
                                for y in r:
                                        cx = x * span2 # corner x
                                        cy = y * span2 # corner y
                                        mean = (
                                                vert[cx][cy] +
                                                vert[cx + span2][cy] +
                                                vert[cx + span2][cy + span2] +
                                                vert[cx][cy + span2]) / 4.0
                                        vert[cx + span][cy + span] = random.gauss(mean, deviation)
                        # Square pass
                        r = range(2**i + 1)
                        for x in r:
                                for y in r:
                                        if x == 0 or x == right or y == 0 or y == right:
                                                dev = deviation / edge_smooth
                                        else:
                                                dev = deviation
                                        left_adjust = (x==0)
                                        top_adjust = (y==0)
                                        cx = x * span2 # corner x
                                        cy = y * span2 # corner y
                                        # vert above corner
                                        mean = (
                                                vert[cx][cy] +
                                                vert[cx][cy - span2 - top_adjust] +
                                                vert[(cx + span) % right][cy - span - top_adjust] +
                                                vert[cx - span - left_adjust][cy - span - top_adjust]) / 4.0
                                        vert[cx][cy - span - top_adjust] = random.gauss(mean, dev)
                                        # vert to left of corner
                                        mean = (
                                                vert[cx][cy] +
                                                vert[cx - span2 - left_adjust][cy] +
                                                vert[cx - span - left_adjust][(cy + span) % right] +
                                                vert[cx - span - left_adjust][cy - span - top_adjust]) / 4.0
                                        vert[cx - span - left_adjust][cy] = random.gauss(mean, dev)
                        deviation /= 1.0 + smooth_step * i

                if seamless:
                        # This is not very good, we need a better method here
                        vert[-1] = vert[0]
                        for i in range(width):
                                vert[i][-1] = vert[i][0]

                # Calculate normals and vertex colors
                self.normal = [[] for i in range(width)]
                self.color = [[] for i in range(width)]
                vlen = float(self.display_width) / self.size
                x1 = vlen; y1 = 2*vlen
                x2 = -vlen; y2 = 2*vlen
                x3 = vlen; y3 = 2*vlen
                x4 = -vlen; y4 = 2*vlen
                tree_relheight = tree_line - water_line
                max_green = tree_relheight * 0.8
                water_transition = tree_relheight
                for x in range(width):
                        for y in range(width):
                                try:
                                        # Make 2 overlapping triangles of surrounding verts
                                        z1 = vert[x + 1][y + 1] - vert[x][y + 1]
                                        z2 = vert[x - 1][y + 1] - vert[x][y + 1]
                                        z3 = vert[x + 1][y - 1] - vert[x][y - 1]
                                        z4 = vert[x - 1][y - 1] - vert[x][y - 1]
                                        # calc unit normal using x-product
                                        nx = y1 * z2 - z1 * y2 + y3 * z4 - z3 * y4
                                        ny = -x1 * z2 + z1 * x2 - x3 * z4 + z3 * x4
                                        nz = x1 * y2 - y1 * x2 + x3 * y4 - y3 * x4
                                        mag = sqrt(nx**2 + ny**2 + nz**2)
                                        self.normal[x].append((nx / mag, ny / mag, nz / mag))
                                except IndexError:
                                        # Fudge normal for the edge
                                        self.normal[x].append((0, 0, 1))
                                        angle = 0
                                r, g, b = self.color_for(x, y)
                                v = random.gauss(1.0, 0.03)
                                self.color[x].append((r * v, g * v, b * v))
        
        def draw_wireframe(self, show_normals=False):
                """Draw terrain mesh with a grid of lines"""
                vlen = float(self.display_width) / self.size
                vert = self.vert
                color = self.color
                glTranslatef(-self.display_width / 2, -self.display_width / 2, 0)
                glBegin(GL_LINES)
                for y in range(self.size):
                        for x in range(self.size):
                                glColor3f(*color[x][y])
                                if x > 0:
                                        glVertex3f((x - 1) * vlen, y * vlen, vert[x - 1][y])
                                        glVertex3f(x * vlen, y * vlen, vert[x][y])
                                if y > 0:
                                        glVertex3f(x * vlen, (y -1) * vlen, vert[x][y - 1])
                                        glVertex3f(x * vlen, y * vlen, vert[x][y])
                                if show_normals and self.normal[x][y] is not None:
                                        glColor3f(0.0, 0.0, 1.0)
                                        nx, ny, nz = self.normal[x][y]
                                        glVertex3f(x * vlen, y * vlen, vert[x][y])
                                        glVertex3f(x * vlen + nx*2, y * vlen + ny*2, vert[x][y] + nz*2)
                glEnd()

        # Colors used for the default color_for implementation below
        sand_r, sand_g, sand_b = (0.6, 0.52, 0.32)
        dirt_r, dirt_g, dirt_b = (0.165, 0.15, 0.12)
        rock_r, rock_g, rock_b = (0.25, 0.28, 0.30)
        grass_r, grass_g, grass_b = (0.10, 0.30, 0.07)
        tree_r, tree_g, tree_b = (0.0, 0.2, 0.08)
        ice_r, ice_g, ice_b = (0.6, 0.7, 0.95)
        snow_r, snow_g, snow_b = (1.0, 1.0, 1.0)
        
        def color_for(self, x, y):
                """Return the color for a given vertex as a 3-tuple of (r, g, b),
                called for each vert after the normal is computed (note normals for
                surrounding verts may not be computed yet).
                """
                sand = rock = dirt = grass = tree = snow = ice = 0.0
                nx, ny, nz = self.normal[x][y]
                v = random.gauss(0, 0.05)
                slope = (sqrt(nx**2 + ny**2) + 0.00001) / nz # Slope is cheaper to compute than the angle
                # Weight the various terrain elements according to slope and elevation
                if slope > 0.8 + v:
                        rock = min((slope+v)**2, 1.0)
                elv = self.vert[x][y]
                if slope > 0.5 + v and elv > self.sand_line + v:
                        dirt = max(min(slope - 0.5 + v, 1.0) - rock, 0.0)
                if elv > self.snow_line + v*10:
                        ice = min(slope + v, 1.0)
                        snowiness = elv - self.snow_line + v
                        snow = max(min(snowiness*abs(snowiness), 1.0), 0.0)
                        ice *= snow
                if (slope <= 0.5 or elv > self.tree_line) and elv < self.sand_line + v:
                        sand = max(1.0 + v - snow, 0.0)
                if elv < self.tree_line + abs(v*25):
                        tree = min(max(random.gauss(slope + elv / (self.tree_line or 0.00001), 0.2)
                                - dirt - rock - sand, 0.0), 1.0)
                        grass = max((0.3 / slope) - dirt - rock - tree, 0.0)
                total = sand + rock + dirt + grass + tree + snow + ice
                if not total: # Catch-all, mix dirt and sand
                        sand = max(min(0.02 / slope, 1.0), 0.0) / 2.0
                        dirt = 1.0 - sand
                        total = sand + rock + dirt + grass + tree + snow + ice
                # Blend the terrain colors according to weight. 
                # TODO make more efficient by using 32bit RGB
                r = (self.sand_r*sand + self.dirt_r*dirt + (self.rock_r)*rock + self.grass_r*grass + 
                        self.tree_r*tree + self.snow_r*snow + self.ice_r*ice) / total
                g = (self.sand_g*sand + self.dirt_g*dirt + (self.rock_g)*rock + self.grass_g*grass + 
                        self.tree_g*tree + self.snow_g*snow + self.ice_g*ice) / total
                b = (self.sand_b*sand + self.dirt_b*dirt + (self.rock_b)*rock + self.grass_b*grass + 
                        self.tree_b*tree + self.snow_b*snow+ self.ice_b*ice) / total
                return (r, g, b)
        
        def draw_solid(self):
                """Draw terrain with shaded polys"""
                glPushMatrix()
                self.performTranslate()
                vlen = float(self.display_width) / self.size
                vert = self.vert
                normal = self.normal
                color = self.color
                glPushMatrix()
                glTranslatef(-self.display_width / 2, -self.display_width / 2, 0)
                glBegin(GL_TRIANGLES)
                glColor3f(0.5, 0.5, 0.5)
                for y in range(1, self.size):
                        for x in range(1, self.size):
                                glNormal3f(*normal[x][y])
                                glColor3f(*color[x][y])
                                glVertex3f(x * vlen, y * vlen, vert[x][y])
                                glNormal3f(*normal[x-1][y-1])
                                glColor3f(*color[x-1][y-1])
                                glVertex3f((x-1) * vlen, (y-1) * vlen, vert[x-1][y-1])
                                glNormal3f(*normal[x][y-1])
                                glColor3f(*color[x][y-1])
                                glVertex3f(x * vlen, (y-1) * vlen, vert[x][y-1])

                                glNormal3f(*normal[x][y])
                                glColor3f(*color[x][y])
                                glVertex3f(x * vlen, y * vlen, vert[x][y])
                                glNormal3f(*normal[x-1][y])
                                glColor3f(*color[x-1][y])
                                glVertex3f((x-1) * vlen, y * vlen, vert[x-1][y])
                                glNormal3f(*normal[x-1][y-1])
                                glColor3f(*color[x-1][y-1])
                                glVertex3f((x-1) * vlen, (y-1) * vlen, vert[x-1][y-1])
                glEnd()
                glPopMatrix()
                glPopMatrix()

        def performTranslate(self):
                glRotatef(90, 1, 0, 0)
        
        def draw(self):
                glPushMatrix()
                """Draw current compiled display list"""
                self.performTranslate()
                glLightfv(GL_LIGHT0, GL_POSITION, fourfv(10, -10, 0, 0)) 
                glCallList(self.display_list)
                glPopMatrix()
        
        def compile(self, wireframe=False):
                """Create display list from terrain mesh"""
                list = glGenLists(1)
                glNewList(list, GL_COMPILE)
                if wireframe:
                        self.draw_wireframe()
                else:
                        self.draw_solid()
                glEndList()
                self.display_list = list
                return self.display_list
        
        water_color = (0, 0.3, 0.6, 0.8)

        def draw_composed(self):
                """Draw composed terrain with water reflection effects"""
                glPushMatrix()
                self.performTranslate()                
                glPushAttrib(GL_STENCIL_BUFFER_BIT | GL_TRANSFORM_BIT | GL_CURRENT_BIT)
                # Draw the terrain above water
                glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, 0, 1, -self.water_line))
                glEnable(GL_CLIP_PLANE0)
                self.draw()

                # Draw the reflection and create a stencil mask
                glPushAttrib(GL_FOG_BIT)
                glPushAttrib(GL_LIGHTING_BIT)
                glEnable(GL_STENCIL_TEST)
                glStencilFunc(GL_ALWAYS, 1, 1)
                glStencilOp(GL_KEEP, GL_INCR, GL_INCR)
                # Use fog to make the reflection less perfect
                glFogfv(GL_FOG_COLOR, (ctypes.c_float * 4)(*self.water_color))
                glFogi(GL_FOG_MODE, GL_LINEAR)
                glFogf(GL_FOG_START, 0)
                glFogf(GL_FOG_END, self.display_width * 4 / 5)
                glEnable(GL_FOG)
                glPushMatrix()
                glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, 0, -1, self.water_line))
                glLightfv(GL_LIGHT0, GL_POSITION, (ctypes.c_float * 4)(0, 0, -1, 0))
                glTranslatef(0.0, 0, self.water_line * 2)
                glScalef(1, 1, -1)
                glFrontFace(GL_CW) # This assumes default front face is wound CCW
                self.draw()
                glFrontFace(GL_CCW)
                glPopMatrix()
                glPopAttrib()

                # Draw underwater terrain, except where masked by reflection
                # Use dense fog for underwater effect
                glFogi(GL_FOG_MODE, GL_EXP)
                glFogf(GL_FOG_DENSITY, 0.05)
                glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
                glClipPlane(GL_CLIP_PLANE0, (ctypes.c_double * 4)(0, 0, -1, self.water_line))
                glStencilFunc(GL_EQUAL, 0, -1)
                self.draw()
                glPopAttrib()

                # Draw the water surface
                glDisable(GL_CLIP_PLANE0)
                width = self.display_width / 2
                glBegin(GL_QUADS)
                glColor4f(0.10, 0.10, 0.1, 0.4)
                glNormal3f(0, 0, 1)
                glVertex3f(width, width, self.water_line)
                glVertex3f(-width, width, self.water_line)
                glVertex3f(-width, -width, self.water_line)
                glVertex3f(width, -width, self.water_line)
                glEnd()

                glPopAttrib()
                glPopMatrix()
                
global screenMessage              
screenMessage = '';
def PrintToScreen(message):        
        global screenMessage
        screenMessage += '[' + message + ']'



def drawText():
        global screenMessage
        glPushMatrix()
        glTranslatef(-100, 0, -650)
        label.color = (0, 0, 0, 255)
        label.text = screenMessage                
        label.draw()
        glPopMatrix()

if __name__ == '__main__':               
        try:
                import psyco
        except ImportError:
                pass
        else:
                psyco.full()

        parser = optparse.OptionParser()
        option = parser.add_option
        option('-i', '--iterations', dest='iterations', type='int', default=7,
                help=('Controls the detail of the terrain mesh. '
                        'Increasing the iteration by one doubles the number of vertices'))
        option('-d', '--deviation', dest='deviation', type='float', default=10.0,
                help=('The height deviation between points in terrain. '
                        'Larger numbers production mountainous terrain'))
        option('-s', '--smoothing', dest='smooth', type='float', default=3.5,
                help=('Controls the reduction in deviation between iterations. '
                        'Smaller numbers produce jagged terrain, larger produce smooth hills. '
                        'Typically > 1, numbers less than one generate a chaotic fractured landscape'))
        option('-e', '--start-elevation', dest='start', type='float', default=5.0,
                help='Mean starting elevation, used to calaulate the terrain corners')
        option('-t', '--tree-line', dest='tree_line', type='float', default=12,
                help=('Maximum elevation of vegitation on mountains, '
                        'Used to determine where green shading ends and rocks and snow begin.'))
        option('-a', '--sand-line', dest='sand_line', type='float', default=2,
                help='Max elevation where ground is sandy.')
        option('-n', '--snow-line', dest='snow_line', type='float', default=12.8,
                help='Minimum snow covered elevation')
        option('-w', '--water-line', dest='water_line', type='float', default=0,
                help='Elevation of "sea level", terrain under this is under water')
        option('-r', '--random-seed', dest='seed', default=None, 
                help=('Random number seed for generating the terrain. Due to the fractal algorithm, '
                'The same seed will generate the same basic terrain topology regardless of the '
                'number of iterations. This allows you to generate multiple equivilant '
                'terrain meshes with different levels of mesh detail or different aesthetic '
                'settings.'))
        option('-f', '--wireframe', dest='wireframe', action='store_true', default=True,
                help='Render mesh as wireframe')
        option('-z', '--width', dest='width', type='int', default=3000,
                help='Overall width of the generated terrain')
        opt, args = parser.parse_args()
        if args: raise optparse.OptParseError('Unrecognized args: %s' % args)
        
        win = pyglet.window.Window(width=800, height=600, resizable=True,
                config=pyglet.gl.Config(stencil_size=1, double_buffer=True, depth_size=24))
        keys = key.KeyStateHandler()
        win.push_handlers(keys)

        zoom = -150
        pressed = False
        xrot = 0
        zrot = 0

        @win.event
        def on_mouse_scroll(x, y, scroll_x, scroll_y):
                global zoom
                zoom -= scroll_y
        
        @win.event
        def on_mouse_press(x, y, button, modifiers):
                global pressed
                pressed = button == pyglet.window.mouse.LEFT
        
        @win.event
        def on_mouse_release(x, y, button, modifiers):
                global pressed
                pressed = not (button == pyglet.window.mouse.LEFT)
        
        @win.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
                global xrot, zrot
                zrot -= dx * 0.3
                xrot += dy * 0.3

        font = pyglet.font.load(None, 18, dpi=72)
        text = pyglet.font.Text(font, 'Calculating Terrain...',
                x=win.width / 2,
                y=win.height / 2,
                halign=pyglet.font.Text.CENTER,
                valign=pyglet.font.Text.CENTER)         
        text.color = (0, 0, 0.8, 1.0)
        glClearColor(0.7, 0.7, 1.0, 1.0)
        glClearDepth(1.0)
        glClearStencil(0)
        win.dispatch_events()
        win.clear()
        text.draw()
        win.flip()

        def resize(width, height):
                if height==0:
                        height=1
                glViewport(0, 0, width, height)
                glMatrixMode(GL_PROJECTION)
                glLoadIdentity()
                gluPerspective(70, 1.0*width/height, 0.1, opt.width * 1.2)
                glMatrixMode(GL_MODELVIEW)
                glLoadIdentity()
        
        win.on_resize=resize       
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
        #glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        fourfv = ctypes.c_float * 4        
        glLightfv(GL_LIGHT0, GL_AMBIENT, fourfv(0.1, 0.1, 0.1, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, fourfv(0.6, 0.6, 0.6, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, fourfv(0.05, 0.05, 0.05, 1.0))
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glDepthFunc(GL_LEQUAL)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glFogfv(GL_FOG_COLOR, fourfv(0.6, 0.55, 0.7, 0.8))
        glFogf(GL_FOG_START, opt.width / 2)
        glFogf(GL_FOG_END, opt.width)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        if not opt.wireframe:
               glEnable(GL_FOG)     

        resize(win.width, win.height)
        clock = pyglet.clock.Clock(30)

        terrain = FractalTerrainMesh(
                iterations=opt.iterations, deviation=opt.deviation, smooth=opt.smooth, 
                seed=opt.seed, start=opt.start, tree_line=opt.tree_line, 
                snow_line=opt.snow_line, water_line=opt.water_line, sand_line=opt.sand_line,
                display_width=opt.width)
        terrain.compile(wireframe=opt.wireframe)
        r = 0.0

        plane = Airfoil()
        plane.changeThrust(20000)

        label = pyglet.text.Label('bla',
                          font_name='Times New Roman',
                          font_size=16,
                          x= - win.width/2.0, y=win.width/2.0,
                          anchor_x='left', anchor_y='top')
      
        CameraType = ['follow', 'fixed']
        currentCamera = CameraType[0]

        while not win.has_exit:
                plane.update()
                win.dispatch_events()
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)      
                glLoadIdentity()
                glPushMatrix()
                
                
                # Handle the different types of Camera's
                if currentCamera == CameraType[0]:
                        att = plane.getAttitude()
                        adjAtt = Quaternion.new_rotate_euler( zrot/180.0*math.pi, xrot/180.0*math.pi, 0.0)
                        cameraAjust = adjAtt * Vector3(-100.0,50.0, 2.0)
                        pos = plane.getPos()
                        eye = pos + cameraAjust
                        zen = adjAtt * Vector3(0.0,1.0,0.0)
                        gluLookAt(eye.x, eye.y, eye.z,
                                  pos.x, pos.y, pos.z,
                                  zen.x, zen.y, zen.z)
                elif currentCamera == CameraType[1]:
                        att = plane.getAttitude()
                        adjAtt = Quaternion.new_rotate_euler( zrot/180.0*math.pi, xrot/180.0*math.pi, 0.0)
                        cameraAjust = att * adjAtt * Vector3(-100.0,50.0, 2.0)
                        pos = plane.getPos()
                        eye = pos + cameraAjust
                        zen = att * adjAtt * Vector3(0.0,1.0,0.0)
                        gluLookAt(eye.x, eye.y, eye.z,
                                  pos.x, pos.y, pos.z,
                                  zen.x, zen.y, zen.z)
                
                
                

               #glLightfv(GL_LIGHT0, GL_POSITION, fourfv(-0.5, 0, 1, 0)) 
                #glLightfv(GL_LIGHT0, GL_POSITION, fourfv(10, 10, 10, 10))
                glFogf(GL_FOG_START, opt.width * 2 / 3)
                glFogf(GL_FOG_END, opt.width)                                
                
                if not opt.wireframe:
                        terrain.draw_composed()
                else:
                        terrain.draw()                                                        
                plane.draw()
                glPopMatrix()                
                
                PrintToScreen('pos = ' + pos.__str__())
                PrintToScreen('vel = ' + plane.getVelocity().__str__())
                PrintToScreen('thrust = ' + plane.getThrust().__str__())
                PrintToScreen('adj = ' + plane.adjust.__str__())
                PrintToScreen('airspeed = ' + plane.getAirSpeed().__str__())
                                

                # Handle key presses
                thrustAdjust = 100
                if keys[key.PAGEUP]:
                        plane.changeThrust(thrustAdjust)
                if keys[key.PAGEDOWN]:
                        plane.changeThrust(-thrustAdjust)
                if keys[key.SPACE]:
                        plane.reset()
                if keys[key.F1]:
                        currentCamera = CameraType[0]
                if keys[key.F2]:
                        currentCamera = CameraType[1]

                if keys[key.DOWN]:
                        plane.adjustPitch(0.01)
                elif keys[key.UP]:
                        plane.adjustPitch(-0.01)
                else:
                        ratio = plane.getElevatorRatio()
                        if ratio > 0.0:
                                plane.adjustPitch(-0.01)
                        elif ratio < 0.0:
                                plane.adjustPitch(0.01)
                        
                if keys[key.RIGHT]:
                        plane.adjustRoll(0.01)
                elif keys[key.LEFT]:
                        plane.adjustRoll(-0.01)
                else:
                        ratio = plane.getAileronRatio()
                        if ratio > 0.0:
                                plane.adjustRoll(-0.01)
                        elif ratio < 0.0:
                                plane.adjustRoll(0.01)
                        
                drawText()
                        
                dt = clock.tick()                
                win.flip()
                screenMessage = ''

        print "fps:  %d" % clock.get_fps()
        



