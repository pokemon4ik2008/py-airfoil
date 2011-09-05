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

PI2=2*math.pi
global object3dLib
if os.name == 'nt':
    object3dLib = cdll.LoadLibrary("bin\object3d.dll")
else:
    object3dLib = cdll.LoadLibrary("bin/object3d.so")

last_cams={}
def draw(bot, view):
    v_type=view.getPlaneView(bot.getId())
    if (bot.TYP, v_type) in meshes:
        for m in meshes[(bot.TYPE, v_type)]:
            glPushMatrix()
            m.draw(bot, view.view_id)
            glPopMatrix()
    else:
        glPushMatrix()
        bot.draw()
        glPopMatrix()

def loadMeshes(mesh_paths, views):
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
        name_lookups.extend([ (path, cls(object3dLib.load(path), views)) for (path, cls) in paths[mesh_key] ])

    name_to_mesh=dict(name_lookups)
    for mesh_key in mesh_paths:
        meshes[mesh_key] = [ name_to_mesh[path] for (path, cls) in paths[mesh_key] ]

class Mesh(object):
    def __init__(self, mesh, views):
        self.mesh=mesh
        for v in views:
            v.push_handlers(self)

    def view_change(self, view_id):
        pass

    def draw(self, bot, view_id):
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
    def __init__(self, mesh, views):
        Mesh.__init__(self, mesh, views)

    def draw(self, bot, view_id):
        try:
            assert 'data/models/cockpit/Circle.001' in name_to_mesh
            drawRotatedMesh(bot, Quaternion.new_rotate_euler(0.0, 0.0, ((bot.getPos().y % 6154.0)/6154)*(2*math.pi)), self.mesh, name_to_mesh['data/models/cockpit/Circle.001'].mesh)
        except:
            print_exc()

class CompassMesh(Mesh):
    def __init__(self, mesh, views):
        Mesh.__init__(self, mesh, views)
        self.__bot_details={}

    def view_change(self, view):
        new_details={}
        for (view_id, bot_id) in self.__bot_details:
            if view_id is not view:
                new_details[(view_id, bot_id)]=self.__bot_details[(view_id, bot_id)]
        self.__bot_details=new_details

    def draw(self, bot, view_id):
        heading=bot.getHeading()
        ident=bot.getId()
        if (view_id, ident) not in self.__bot_details:
            self.__bot_details[(view_id, ident)]=(heading, 0.0, manage.now)

        (last_heading, speed, last_update) = self.__bot_details[(view_id, ident)]
        #handle wrapping by calculating the heading when greating than last_heading and when less
        if heading > last_heading:
            alt_heading = heading - PI2
        else:
            alt_heading = heading + PI2
        if math.fabs(heading - last_heading) > math.fabs(alt_heading - last_heading):
            heading=alt_heading

        interval=manage.now-last_update
        if heading > last_heading:
            if speed>=0:
                speed += interval*0.00075
            else:
                speed += interval*0.001            
        else:
            if heading < last_heading:
                if speed<=0:
                    speed -= interval*0.00075
                else:
                    speed -= interval*0.001
        spd_limit=math.pi/14 * interval
        #print 'comp: last: '+str(last_heading)+' cur: '+str(heading)+' spd: '+str(speed)+' tm: '+str(manage.now-last_update)+' ltd: '+str(spd_limit)
        if speed>spd_limit:
            #print 'hit spd_limit 1'
            speed=spd_limit
        else:
            if speed<-spd_limit:
                #print 'hit spd_limit 2'
                speed=-spd_limit
        last_heading+=speed
        last_heading = last_heading % PI2
        last_update=manage.now
        drawRotatedMesh(bot, Quaternion.new_rotate_euler(-last_heading, 0.0, 0.0), self.mesh, name_to_mesh['data/models/cockpit/Cylinder.002'].mesh)
        self.__bot_details[(view_id, ident)]=(last_heading, speed, last_update)
