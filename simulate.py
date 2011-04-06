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
import manage
from proxy import *
from pyglet.gl import *
from pyglet import window, font, clock # for pyglet 1.0
from pyglet.window import key
from control import *
from euclid import *
import sys
from terrain import FractalTerrainMesh
from threading import Condition
from time import sleep
from view import View
from terrain2 import *

global listNum
listNum = glGenLists(1)
def genListNum():
	global listNum
	num=listNum
	listNum+=1
	return num

def genTerrain():
	terrainNum=genListNum()
	glNewList(terrainNum, GL_COMPILE)
	if not opt.wireframe:
		terrain.draw_composed()
	else:
		terrain.draw()                                                        
	glEndList()
	return terrainNum

if __name__ == '__main__':               
	man=manage
        try:
                import psyco
        except ImportError:
		print "failed to import psyco\n"
                pass
        else:
		print "running psyco\n"
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
        option('-r', '--random-seed', dest='seed', default=123456, 
                help=('Random number seed for generating the terrain. Due to the fractal algorithm, '
                'The same seed will generate the same basic terrain topology regardless of the '
                'number of iterations. This allows you to generate multiple equivilant '
                'terrain meshes with different levels of mesh detail or different aesthetic '
                'settings.'))
        option('-f', '--wireframe', dest='wireframe', action='store_true', default=True,
                help='Render mesh as wireframe')
        option('-z', '--width', dest='width', type='int', default=3000,
                help='Overall width of the generated terrain')
        option('-2', '--two', dest='two_player', action='store_true', default=False,
                help='Two player split screen action')
        option('-S', '--server', dest='server', type='str', default=None,
                help='Create a server using at this IP / domain')
        option('-C', '--client', dest='client', type='str', default=None,
                help='Create a client connection this a server at this IP / domain')
        opt, args = parser.parse_args()
        if args: raise optparse.OptParseError('Unrecognized args: %s' % args)

	if opt.server is None:
		if opt.client is None:
			man.server=Server()
			man.proxy=Client()
		else:
			man.proxy=Client(server=opt.client)
	else:
		if opt.client is None:
			man.server=Server(server=opt.server, own_thread=False)
			exit(0)
		else:
			man.server=Server(server=opt.server)
			man.proxy=Client(server=opt.client)
	Sys.init(man.proxy)

        #zoom = -150
        #pressed = False
        #xrot = 0
        #zrot = 0
	#win_planes=[]
	win_width=800
	win_height=600
	config_template=pyglet.gl.Config(stencil_size=1, double_buffer=True, depth_size=24)
	win = pyglet.window.Window(width=win_width, height=win_height, resizable=True, config=config_template)
	win.dispatch_events()
	win.clear()
	win.flip()

	views = []
	def resize(width, height):
		for view in views:
			view.activate()
		return pyglet.event.EVENT_HANDLED

	win.on_resize=resize       
	glClearColor(0.7, 0.7, 1.0, 1.0)
	glClearDepth(1.0)
	glClearStencil(0)
	font = pyglet.font.load(None, 18, dpi=72)
	text = pyglet.font.Text(font, 'Calculating Terrain...',
		 x=win_width / 2,
		 y=win_height / 2,
		 halign=pyglet.font.Text.CENTER,
		 valign=pyglet.font.Text.CENTER)         
	text.color = (0, 0, 0.8, 1.0)
	text.draw()
	glEnable(GL_COLOR_MATERIAL)
	glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
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
	print "width: "+str(win_width)+" height: "+str(win_height)
	resize(win.width, win.height)
        clock = pyglet.clock.Clock()

        terrain = FractalTerrainMesh(
                iterations=opt.iterations, deviation=opt.deviation, smooth=opt.smooth, 
                seed=opt.seed, start=opt.start, tree_line=opt.tree_line, 
                snow_line=opt.snow_line, water_line=opt.water_line, sand_line=opt.sand_line,
                display_width=opt.width)
        terrain.compile(wireframe=opt.wireframe)
        r = 0.0

	win_ctrls=Controller([(Controller.TOG_MOUSE_CAP, KeyAction(key.M, onPress=True))], win)

	player_keys = [Controller([(Controller.THRUST, KeyAction(key.E, key.Q)),
				       (Controller.PITCH, KeyAction(key.S, key.W)),
				       (Controller.ROLL, KeyAction(key.A, key.D)),
				       (Controller.CAM_FIXED, KeyAction(key._1)),
				       (Controller.CAM_FOLLOW, KeyAction(key._2)),
				       (Controller.CAM_Z, KeyAction(key.V, key.F)),
				       (Controller.CAM_X, KeyAction(key.Z, key.X))], 
				      win)]
	if opt.two_player == True:
		player_keys.append(Controller([(Controller.THRUST, KeyAction(key.PAGEDOWN, key.PAGEUP)),
					 (Controller.CAM_FIXED, KeyAction(key._9)),
					 (Controller.CAM_FOLLOW, KeyAction(key._0)), 
					 (Controller.PITCH, MouseAction(-0.00010, MouseAction.Y)),
					 (Controller.ROLL, MouseAction(-0.00010, MouseAction.X)),
					 (Controller.CAM_X, KeyAction(key.O, key.P)), 
					 (Controller.CAM_Z, MouseAction(-0.0025, MouseAction.Z))], 
					win))
		

	planes = {}
	init_positions = [Point3(100,0,100), Point3(-100,0,0)]
        init_attitude = Quaternion.new_rotate_euler( 0.0 /180.0*math.pi, 0.0 /180.0 * math.pi, 0.0 /180.0*math.pi)
	init_thrust = 0
	init_vel = Vector3(0,0,0)

	for i in range(len(player_keys)):
		controller=player_keys[i]
		pos=init_positions[i]
		plane = MyAirfoil(pos, init_attitude, init_vel, init_thrust, controller, man.proxy)
		planes[plane.getId()]=plane

		view = View(controller, win, plane, len(player_keys), opt)
		views.append(view)

	t=genTerrain()
	mouse_cap=False
	bots=[]
	terrain = RandomTerrain(8, 10.0, 1.0)

	try:
		while man.proxy.alive():
			# move this loop to ProxyObs.loop
			for plane in planes.itervalues():
				if plane.alive():
					plane.update()
					plane.markChanged()
			sleep(0)
			win.dispatch_events()

			if win.has_exit:
				for obj in  planes.itervalues():
					obj.markDead()
					obj.markChanged()
				man.proxy.markDead()
				man.proxy.markChanged()

			if win_ctrls.eventCheck(win_ctrls.getControls())[Controller.TOG_MOUSE_CAP]!=0:
				mouse_cap = ~mouse_cap
				win.set_exclusive_mouse(mouse_cap)
				win_ctrls.clearEvents(win_ctrls.getControls())

			if man.proxy.acquireLock():
				bots[:]= man.proxy.getTypeObjs(ControlledSer.TYP)
				man.proxy.releaseLock()

			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)      
			for view in views:
				glLoadIdentity()
				view.activate()
				if view.getPlaneId() in planes:
					my_plane=planes[view.getPlaneId()]
					view.printToScreen('pos = ' + str(my_plane.getPos()))
					view.printToScreen('vel = ' + str(my_plane.getVelocity()))
					view.printToScreen('thrust = ' + str(my_plane.getThrust()))
					view.printToScreen('airspeed = ' + str(my_plane.getAirSpeed()))
					view.printToScreen("heading = " + str(my_plane.getHeading()/math.pi*180.0))

				#glCallList(t)
				terrain.draw(view)

				for bot in bots:
					if bot.alive():
						glPushMatrix()
						#planes[bot.getId()].draw()
						bot.draw()
						glPopMatrix()

				view.eventCheck()
				glLoadIdentity()
				view.drawText()
				dt=clock.tick()

			for bot in bots:
				if not bot.alive() and bot.getId() in planes:
					del planes[bot.getId()]

			for plane in planes.itervalues():
				if plane.alive():
					plane.eventCheck()

			if planes==[]:
				break
			win.flip()
	except Exception:
		print_exc
		man.proxy.markDead()
		man.proxy.markChanged()
        print "fps:  %d" % clock.get_fps()
	print 'before proxy.join'
	if man.proxy:
		man.proxy.join(3)
		try:
			assert not man.proxy.isAlive()
		except:
			print_exc()
	if man.server:
		man.server.join(1)
		try:
			assert not man.server.isAlive()
		except:
			print_exc()
	print 'quitting main thread'
