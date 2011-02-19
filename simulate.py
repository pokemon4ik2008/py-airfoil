#!/usr/bin/env python

##//
##//    Copyright 2011 Paul White
##//
##//    This file is part of py-airfoil.
##//
##//    This is free software: you can redistribute it and/or modify
##//    it under the terms of the GNU General Public License as published by
##//    the Free Software Foundation, either version 3 of the License, or
##//    (at your option) any later version.
##
##//    This is distributed in the hope that it will be useful,
##//    but WITHOUT ANY WARRANTY; without even the implied warranty of
##//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##//    GNU General Public License for more details.
##//
##//    You should have received a copy of the GNU General Public License
##//    along with FtpServerMobile.  If not, see <http://www.gnu.org/licenses/>.
##//

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
from terrain import FractalTerrainMesh
                
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
        



