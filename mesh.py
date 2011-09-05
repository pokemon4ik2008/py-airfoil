import ctypes
from ctypes import *
from euclid import *
import glob
import itertools
from math import degrees
import os
from traceback import print_exc

import manage
from pyglet.gl import *

global object3dLib
if os.name == 'nt':
    object3dLib = cdll.LoadLibrary("bin\object3d.dll")
else:
    object3dLib = cdll.LoadLibrary("bin/object3d.so")

    def draw(bot, v_type):
        if (bot.TYP, v_type) in meshes:
            for m in meshes[(bot.TYPE, v_type)]:
                glPushMatrix()
                m.draw(bot)
                glPopMatrix()
        else:
            glPushMatrix()
            bot.draw()
            glPopMatrix()

def loadMeshes(mesh_paths):
    lookup = {}
    global meshes
    meshes = {}
    global name_to_mesh
    name_to_mesh = {}
    paths = {}
    if os.name == 'nt':
        convert=lambda s: re.sub(r'/', r'\\', s)
    else:
        convert=lambda s: s

    for mesh_key in mesh_paths:
        paths[mesh_key]=dict(itertools.chain(*[ [ (path, cls) for path in glob.glob(convert(glob_path)) ] for (glob_path, cls) in mesh_paths[mesh_key] ])).items()

    name_lookups=[]
    for mesh_key in mesh_paths:
        name_lookups.extend([ (path, cls(object3dLib.load(path))) for (path, cls) in paths[mesh_key] ])

    name_to_mesh=dict(name_lookups)
    for mesh_key in mesh_paths:
        meshes[mesh_key] = [ name_to_mesh[path] for (path, cls) in paths[mesh_key] ]

class Mesh(object):
    def __init__(self, mesh):
        self.mesh=mesh

    def draw(self, bot):
        # Apply rotation based on Attitude, and then rotate by constant so that model is orientated correctly
        angleAxis = (bot.getAttitude() * Quaternion.new_rotate_axis(math.pi/2.0, Vector3(0,0,1)) * Quaternion.new_rotate_axis(math.pi/2.0, Vector3(0,1,0)) ).get_angle_axis()
        axis = angleAxis[1].normalized()
        
        fpos = (c_float * 3)()
        fpos[0] = bot._pos.x
        fpos[1] = bot._pos.y
        fpos[2] = bot._pos.z
        object3dLib.setPosition(fpos)
        
        fpos[0] = axis.x
        fpos[1] = axis.y
        fpos[2] = axis.z
        
        object3dLib.setAngleAxisRotation(c_float(degrees(angleAxis[0])), fpos)
        object3dLib.draw(self.mesh)            

def drawRotatedMesh(bot, angle_quat, drawing_mesh, centre_mesh):
        att=bot.getAttitude()
        axisRotator=Quaternion.new_rotate_axis(math.pi/2.0, Vector3(0,0,1)) * Quaternion.new_rotate_axis(math.pi/2.0, Vector3(0,1,0))
        angleAxis= (att * angle_quat * axisRotator ).get_angle_axis()
        
        mid = (c_float * 3)()
        object3dLib.getMid(centre_mesh, mid)
        midPt=Vector3(mid[0], mid[1], mid[2]) * 100
        rotOrig=(att * axisRotator * (midPt))
        rotNew=(att * angle_quat * axisRotator * (midPt))

        axis = angleAxis[1].normalized()
        c=bot.getPos()-(rotNew-rotOrig)

        fpos = (c_float * 3)()
        fpos[0] = c.x
        fpos[1] = c.y
        fpos[2] = c.z
        object3dLib.setPosition(fpos)
        
        fpos[0] = axis.x
        fpos[1] = axis.y
        fpos[2] = axis.z
            
        object3dLib.setAngleAxisRotation(c_float(degrees(angleAxis[0])), fpos)
        object3dLib.draw(drawing_mesh)
        
class AltMeterMesh(Mesh):
    def __init__(self, mesh):
        Mesh.__init__(self, mesh)

    def draw(self, bot):
        try:
            assert 'data/models/cockpit/Circle.001' in name_to_mesh
            drawRotatedMesh(bot, Quaternion.new_rotate_euler(0.0, 0.0, ((bot.getPos().y % 6154.0)/6154)*(2*math.pi)), self.mesh, name_to_mesh['data/models/cockpit/Circle.001'].mesh)
        except:
            print_exc()

class CompassMesh(Mesh):
    def __init__(self, mesh):
        Mesh.__init__(self, mesh)
        self.__last_heading=math.pi*1.5
        self.__speed=0
        self.__last_update=manage.now

    def draw(self, bot):
        heading=bot.getHeading()
        
        full_rot=2*math.pi
        #handle wrapping by calculating the heading when greating than last_heading and when less
        if heading > self.__last_heading:
            alt_heading = heading - full_rot
        else:
            alt_heading = heading + full_rot
        if math.fabs(heading - self.__last_heading) > math.fabs(alt_heading - self.__last_heading):
            heading=alt_heading

        interval=manage.now-self.__last_update
        if heading > self.__last_heading:
            if self.__speed>=0:
                self.__speed += interval*0.00075
            else:
                self.__speed += interval*0.001            
        else:
            if heading < self.__last_heading:
                if self.__speed<=0:
                    self.__speed -= interval*0.00075
                else:
                    self.__speed -= interval*0.001
        spd_limit=math.pi/12 * interval
        #print 'comp: last: '+str(self.__last_heading)+' cur: '+str(heading)+' spd: '+str(self.__speed)+' tm: '+str(manage.now-self.__last_update)+' ltd: '+str(spd_limit)
        if self.__speed>spd_limit:
            self.__speed=spd_limit
        else:
            if self.__speed<-spd_limit:
                self._speed=-spd_limit
        self.__last_heading+=self.__speed
        self.__last_heading = self.__last_heading % full_rot
        self.__last_update=manage.now
        drawRotatedMesh(bot, Quaternion.new_rotate_euler(-self.__last_heading, 0.0, 0.0), self.mesh, name_to_mesh['data/models/cockpit/Cylinder.002'].mesh)
