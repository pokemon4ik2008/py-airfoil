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
from airfoil import Airfoil, Obj
import os
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
import traceback
from view import View
from skybox import *

global listNum
global opt

def loadTerrain():
	global cterrain
	colFileName = ''
	mapFileName = ''
	if os.name == 'nt':
		cterrain = cdll.LoadLibrary("bin\cterrain.dll")
		colFileName = "data\\strip1.bmp"
		mapFileName = "data\\map_output.hm2"
	else:
		cterrain = cdll.LoadLibrary("bin/cterrain.so")
		colFileName = "data/strip1.bmp" 
		mapFileName = "data/map_output.hm2"

	cterrain.init(c_char_p(colFileName), 
		      c_char_p(mapFileName), 
		      c_float(4.0/3.0*2.0),
		      c_int(0),
		      c_float(10.0),
		      c_float(0.2))

def drawTerrain(view):
	pointOfView = (c_float * 6)()
	cameraVectors = view.getCamera().getCameraVectors()
        cameraCenter = cameraVectors[0]
        cameraPosition = cameraVectors[1]
	pointOfView[0] = cameraPosition[0]
	pointOfView[1] = cameraPosition[1]
	pointOfView[2] = cameraPosition[2]
	pointOfView[3] = cameraCenter[0]
	pointOfView[4] = cameraCenter[1]
	pointOfView[5] = cameraCenter[2]
	cterrain.draw(pointOfView)

class Bullet(Obj, ControlledSer):
    TYP=3
    #LIFE_SPAN is in seconds
    LIFE_SPAN=30 
    __IN_FLIGHT=set()

    @classmethod
    def getInFlight(cls):
        return cls.__IN_FLIGHT

    def __init__(self, ident=None, pos = Vector3(0,0,0), attitude = Vector3(0,0,0), vel = Vector3(0,0,0), proxy=None):
        Obj.__init__(self, pos=pos, attitude=attitude, vel=vel)
        self._mass = 1.0 # 100g -- a guess
        self._scales = [0.032, 0.032, 0.005]
        ControlledSer.__init__(self, Bullet.TYP, ident, proxy=proxy)

    def localInit(self):
        ControlledSer.localInit(self)
	(self._just_born, self._just_dead)=(True, False)
	self.__start=manage.now
	if self not in Bullet.__IN_FLIGHT:
		Bullet.__IN_FLIGHT.add(self)
		if(len(self.__class__.__IN_FLIGHT)%25==0):
			print 'num bullets (more): '+str(len(self.__class__.__IN_FLIGHT))

    def markDead(self):
	    ControlledSer.markDead(self)
            if self in Bullet.__IN_FLIGHT:
       		    self._just_dead=True	
                    Bullet.__IN_FLIGHT.remove(self)
                    if(len(self.__class__.__IN_FLIGHT)%25==0):
                        print 'num bullets (fewer): '+str(len(self.__class__.__IN_FLIGHT))

    def isClose(self, obj):
        return obj.getId()==self.getId()

    def _updateVelFromEnv(self, timeDiff):
        self._updateVelFromGrav(timeDiff)
        #Drag, acts || to Velocity vector
        dv  = self.getDragForce(timeDiff) * timeDiff / self._mass
        self._velocity -= dv

    def _updateFromEnv(self, timeDiff):
        self._updateVelFromEnv(timeDiff)

    def getDragForce(self, drag=0.0): 
	    return self._velocity * 0.05

    def update(self):
        if self.getId() in self._proxy:
            rs=self._proxy.getObj(self.getId()) #rs = remote_self
            (self._pos, self._attitude, self._velocity)=(rs._pos, rs._attitude, rs._velocity)

	if manage.now-self.__start > Bullet.LIFE_SPAN or self.getPos().y<=0:
            self.markDead()
            self.markChanged()

    def estUpdate(self):
        timeDiff=self._getTimeDiff()
	self._updateFromEnv(timeDiff)
        self._updatePos(timeDiff)
  
    def serialise(self):
	    (self._just_born, self._just_dead) = (False, False)
	    return ControlledSer.serialise(self)

    def justBornOrDead(self):
	    return self._just_born or self._just_dead

    def draw(self):
        try:
            assert self.alive()
            pos = self.getPos()
            glDisable(GL_CULL_FACE)
            glTranslatef(pos.x, pos.y, pos.z)
            glBegin(GL_POINTS)
            glColor4f(1.0,1.0,1.0,1.0)
	    glVertex3f(0,0,0)
            glEnd()
        except AssertionError:
            print_exc()

class MyAirfoil(Airfoil, ControlledSer):
    TYP=0

    def __init__(self, controls=None, proxy=None, 
                 pos = Vector3(0,0,0), 
                 attitude = Vector3(0,0,0), 
                 velocity = Vector3(0,0,0), 
                 thrust = 0, ident=None):
        Airfoil.__init__(self, pos, attitude, velocity, thrust)
        ControlledSer.__init__(self, MyAirfoil.TYP, ident, proxy)
        print 'MyAirfoil. initialised airfoil thrust '+str(thrust)
        self.__controls=controls

    def localInit(self):
        ControlledSer.localInit(self)
        self.__interesting_events = [Controller.THRUST, Controller.PITCH, Controller.ROLL, Controller.FIRE]
        self.__thrustAdjust = 100
        self.__pitchAdjust = 0.01
        self.__rollAdjust = 0.01
        self.__bullets=[]
        self.__last_fire=manage.now

    def remoteInit(self, ident):
        ControlledSer.remoteInit(self, ident)
        self.__lastKnownPos=Vector3(0,0,0)
        self.__lastDelta=Vector3(0,0,0)
        #self.__lastKnownAtt=Quaternion(1,0,0,0)
        #self.__lastAttDelta=Quaternion(1,0,0,0)
        self.__lastUpdateTime=0.0

    def estUpdate(self):
        period=manage.now-self.__lastUpdateTime
        self.setPos(self.__lastKnownPos+
                    (self.__lastDelta*period))
        return self

    def eventCheck(self):
        if not Controls:
            raise NotImplementedError
        events = self.__controls.eventCheck(self.__interesting_events)

        self.changeThrust(events[Controller.THRUST]*self.__thrustAdjust)
        if events[Controller.PITCH]!=0:
            self.adjustPitch(events[Controller.PITCH]*self.__pitchAdjust)
        if events[Controller.ROLL]!=0:
            self.adjustRoll(-events[Controller.ROLL]*self.__rollAdjust)
        if events[Controller.FIRE]!=0 and manage.now-self.__last_fire>Airfoil._FIRING_PERIOD:
            vOff=self.getVelocity().normalized()*800
            b=Bullet(pos=self.getPos().copy(), attitude=self.getAttitude().copy(), vel=self.getVelocity()+vOff, proxy=self._proxy)
            b.update()
            b.markChanged()
            self.__last_fire=manage.now
        self.__controls.clearEvents(self.__interesting_events)

    def serialise(self):
        ser=Mirrorable.serialise(self)
        p=self.getPos()
        ser.append(p.x)
        ser.append(p.y)
        ser.append(p.z)
        a=self.getAttitude()
        ser.append(a.w)
        ser.append(a.x)
        ser.append(a.y)
        ser.append(a.z)
        return ser

    def deserialise(self, ser, estimated=False):
        (px, py, pz)=ControlledSer.vAssign(ser, ControlledSer._POS)
        (aw, ax, ay, az)=ControlledSer.qAssign(ser, ControlledSer._ATT)
        
        if not estimated:
            now=manage.now
            period=now-self.__lastUpdateTime
            pos=Vector3(px,py,pz)
            self.__lastDelta=(pos-self.__lastKnownPos)/period
            self.__lastUpdateTime=now
            self.__lastKnownPos=pos
        return Mirrorable.deserialise(self, ser, estimated).setPos(Vector3(px,py,pz)).setAttitude(Quaternion(aw,ax,ay,az))

def simMain():
	man=manage
        #try:
        #        import psyco
        #except ImportError:
	#	print "failed to import psyco\n"
        #        pass
        #else:
	#	print "running psyco\n"
        #        psyco.full()

        parser = optparse.OptionParser()
        option = parser.add_option
        option('-z', '--width', dest='width', type='int', default=3000,
                help='Overall width of the generated terrain')

        option('-2', '--two', dest='two_player', action='store_true', default=False,
                help='Two player split screen action')
        option('-S', '--server', dest='server', type='str', default=None,
                help='Create a server using at this IP / domain')
        option('-C', '--client', dest='client', type='str', default=None,
                help='Create a client connection this a server at this IP / domain')
        man.opt, args = parser.parse_args()
        if args: raise optparse.OptParseError('Unrecognized args: %s' % args)

	factory=SerialisableFact({ MyAirfoil.TYP: MyAirfoil, Bullet.TYP: Bullet })
	if man.opt.server is None:
		if man.opt.client is None:
			man.server=Server()
			man.proxy=Client(factory=factory)
		else:
			man.proxy=Client(server=man.opt.client, factory=factory)
	else:
		if man.opt.client is None:
			man.server=Server(server=man.opt.server, own_thread=False)
			exit(0)
		else:
			man.server=Server(server=man.opt.server)
			man.proxy=Client(server=man.opt.client, factory=factory)
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
			view.updateDimensions()
		return pyglet.event.EVENT_HANDLED

	win.on_resize=resize       
	glClearColor(1.0, 1.0, 1.0, 1.0)
	glClearDepth(1.0)
	glClearStencil(0)
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
	glEnable(GL_POINT_SMOOTH)
	glPointSize(2)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

	#glFogfv(GL_FOG_COLOR, fourfv(0.6, 0.55, 0.7, 0.8))
	#glFogf(GL_FOG_START, opt.width / 2)
	#glFogf(GL_FOG_END, opt.width)
	#glFogi(GL_FOG_MODE, GL_LINEAR)

	#if not opt.wireframe:
	glEnable(GL_FOG)     
	print "width: "+str(win_width)+" height: "+str(win_height)
	resize(win.width, win.height)
        clock = pyglet.clock.Clock()

        r = 0.0

	win_ctrls=Controller([(Controller.TOG_MOUSE_CAP, KeyAction(key.M, onPress=True))], win)

	player_keys = [Controller([(Controller.THRUST, KeyAction(key.E, key.Q)),
				   (Controller.FIRE, KeyAction(key.R)),
				   (Controller.PITCH, KeyAction(key.S, key.W)),
				   (Controller.ROLL, KeyAction(key.A, key.D)),
				   (Controller.CAM_FIXED, KeyAction(key._1)),
				   (Controller.CAM_FOLLOW, KeyAction(key._2)),
				   (Controller.CAM_Z, KeyAction(key.V, key.Z)),
				   (Controller.CAM_X, KeyAction(key.Z, key.X))], 
		       win)]
	if man.opt.two_player == True:
		player_keys.append(Controller([(Controller.THRUST, KeyAction(key.PAGEDOWN, key.PAGEUP)),
					       (Controller.FIRE, MouseButAction(MouseButAction.LEFT)),
					       (Controller.CAM_FIXED, KeyAction(key._9)),
					       (Controller.CAM_FOLLOW, KeyAction(key._0)), 
					       (Controller.PITCH, MouseAction(-0.00010, MouseAction.Y)),
					       (Controller.ROLL, MouseAction(-0.00010, MouseAction.X)),
					       (Controller.CAM_X, KeyAction(key.O, key.P)), 
					       (Controller.CAM_Z, MouseAction(-0.0025, MouseAction.Z))], 
					      win))
		

	planes = {}
	plane_inits=[(Point3(100,0,100), 
		      Quaternion.new_rotate_euler( 0.0 /180.0*math.pi, 0.0 /180.0 * math.pi, 0.0 /180.0*math.pi), 
		      Vector3(0,0,0),
		      0),
		     (Point3(-100,0,0), 
		      Quaternion.new_rotate_euler( 0.0 /180.0*math.pi, 0.0 /180.0 * math.pi, 0.0 /180.0*math.pi), 
		      Vector3(0,0,0),
		      0)]

	for i in range(len(player_keys)):
		controller=player_keys[i]
		(pos, att, vel, thrust)=plane_inits[i]
		plane = MyAirfoil(pos=pos, attitude=att, velocity=vel, thrust=thrust, 
				  controls=controller, proxy=man.proxy)
		planes[plane.getId()]=plane

		view = View(controller, win, plane, len(player_keys), man.opt)
		views.append(view)

	mouse_cap=False
	bots=[]
	loadTerrain()
	skybox = Skybox()

	start_time=time()
	try:
		while man.proxy.alive():
			man.now=time()

			# move this loop to ProxyObs.loop
			[ plane.update() for plane in planes.itervalues() if plane.alive() ]
			[ b.update() for b in set(Bullet.getInFlight())]

			if man.proxy.acquireLock():
				bots[:]= man.proxy.getTypesObjs([ MyAirfoil.TYP, Bullet.TYP ]) 
				[ b.estUpdate() for b in bots ]
				man.proxy.releaseLock()

			[ plane.markChanged() for plane in planes.itervalues() if plane.alive() ]
			[ b.markChanged() for b in Bullet.getInFlight() if b.justBornOrDead() ]

			win.dispatch_events()
			if win.has_exit:
				print 'exiting window'
				for obj in planes.itervalues():
					obj.markDead()
					obj.markChanged()
				man.proxy.markDead()
				man.proxy.markChanged()

			if win_ctrls.eventCheck()[Controller.TOG_MOUSE_CAP]!=0:
				mouse_cap = ~mouse_cap
				win.set_exclusive_mouse(mouse_cap)
				win_ctrls.clearEvents()

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

                                skybox.draw(view)
				drawTerrain(view)
				

				for bot in bots:
					if bot.alive():
						glPushMatrix()
						bot.draw()
						glPopMatrix()

				view.eventCheck()
				glLoadIdentity()
				view.drawText()
				dt=clock.tick()

			for bot in bots:
			       	if not bot.alive() and bot.getId() in planes:
					del planes[bot.getId()]

			[ plane.eventCheck() for plane in planes.itervalues() if plane.alive() ]

			if planes==[]:
				break
			win.flip()
	except Exception as detail:
		print str(detail)
		traceback.print_exc()
		man.proxy.markDead()
		man.proxy.markChanged()
	print 'before proxy.join'
	if man.proxy:
		flush_start=time()
		while not man.proxy.attemptSendAll():
			if time()-flush_start>3:
				break
			sleep(0)
		man.proxy.join(3)
		try:
			assert not man.proxy.isAlive()
		except:
			print_exc()
	if man.server:
		man.server.join(3)
		try:
			assert not man.server.isAlive()
		except:
			print_exc()
	print 'quitting main thread'
        print "fps:  %d" % clock.get_fps()
	end_time=time()
	if man.proxy:
		print "client: kb/s read: "+str((man.proxy.bytes_read/1024)/(end_time-start_time))+' sent: '+str((man.proxy.bytes_sent/1024)/(end_time-start_time))
	if man.server:
		print "server: kb/s read: "+str((man.server.bytes_read/1024)/(end_time-start_time))+' sent: '+str((man.server.bytes_sent/1024)/(end_time-start_time))
	if SerialisableFact.TOT_CNT>0:
		print 'hits: '+str(SerialisableFact.HIT_CNT)+' '+str(SerialisableFact.TOT_CNT)+' ratio: '+str(SerialisableFact.HIT_CNT/float(SerialisableFact.TOT_CNT))
	else:
		print 'hits: '+str(SerialisableFact.HIT_CNT)+' '+str(SerialisableFact.TOT_CNT)

if __name__ == '__main__':
	simMain()

