import ctypes
from ctypes import *
from euclid import *
import glob
import itertools
from math import degrees
import os

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
        global meshes
        meshes = {}
	paths = {}
        if os.name == 'nt':
            convert=lambda s: re.sub(r'/', r'\\', s)
        else:
            convert=lambda s: s
        for mesh_key in mesh_paths:
            paths[mesh_key]=dict(itertools.chain(*[ [ (path, cls) for path in glob.glob(convert(glob_path)) ] for (glob_path, cls) in mesh_paths[mesh_key] ])).items()
	for mesh_key in mesh_paths:
            meshes[mesh_key] = [ cls(object3dLib.load(path)) for (path, cls) in paths[mesh_key] ]

class Mesh(object):
    def __init__(self, mesh):
        self.__mesh=mesh

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
            object3dLib.draw(self.__mesh)            

class CompassMesh(Mesh):
    def __init__(self, mesh):
        Mesh.__init__(self, mesh)

    def draw(self, bot):
        Mesh.draw(self, bot)
