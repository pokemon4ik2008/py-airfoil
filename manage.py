import os
from ctypes import *

from async import Scheduler

global worker
worker=Scheduler(block=False)
global proxy
proxy=None
global server
server=None
global fast_path
fast_path=True
global sound_effects
sound_effects=False
global opt
global vbo
vbo=False
from time import time
global now, delta, iteration
iteration=0
global lookup_colliders
global object3dLib
if os.name == 'nt':
    object3dLib = cdll.LoadLibrary("bin\object3d.dll")
    cterrain = cdll.LoadLibrary("bin\cterrain.dll")
else:
    object3dLib = cdll.LoadLibrary("bin/libobject3d.so")
    cterrain = cdll.LoadLibrary("bin/libcterrain.so")

cterrain.checkCollision.argtypes=[ c_void_p, c_void_p, POINTER(c_uint) ]
cterrain.checkCollision.restype=c_bool

object3dLib.setupRotation.argtypes=[ c_double, c_double, c_double,
                                     c_double, c_double, c_double, c_double,
                                     c_double, c_double, c_double,
                                     c_double, c_double, c_double ]
object3dLib.setupRotation.restype=None

collider.checkCollisionCol.argtypes=[ c_void_p, c_void_p,
                                         c_void_p, POINTER(c_uint),
                                         c_void_p, POINTER(c_uint)]
collider.checkCollisionCol.restype=c_bool

collider.checkCollisionPoint.argtypes=[ c_void_p,
                                           c_double, c_double, c_double,
                                           c_double, c_double, c_double,
                                           c_void_p, POINTER(c_uint) ]
collider.checkCollisionPoint.restype=c_bool

object3dLib.allocTransCols.argtypes=[ c_void_p ]
object3dLib.allocTransCols.restype=c_void_p

object3dLib.load.argtypes=[ c_char_p, c_float ]
object3dLib.load.restype=c_void_p

object3dLib.deleteMesh.argtypes=[ c_void_p ]
object3dLib.deleteMesh.restype=None

object3dLib.getUvPath.argtypes=[ c_void_p, c_uint ]
object3dLib.getUvPath.restype=c_char_p

object3dLib.getMeshPath.argtypes=[ c_void_p ]
object3dLib.getMeshPath.restype=c_char_p

object3dLib.setupTex.argtypes=[ c_void_p, c_uint, c_uint ]
object3dLib.setupTex.restype=c_uint

object3dLib.createTexture.argtypes=[ c_void_p, c_uint, c_void_p, c_uint, c_uint, c_uint ]
object3dLib.createTexture.restype=c_uint

object3dLib.createFBO.argtypes=[ c_uint, c_uint, c_uint ]
object3dLib.createFBO.restype=c_uint

object3dLib.drawToTex.argtypes=[ c_void_p, c_float, c_uint, c_uint, c_uint, c_uint, c_uint, c_uint ]
object3dLib.drawToTex.restype=None

object3dLib.draw.argtypes=[ c_void_p, c_float ]
object3dLib.draw.restype=None

object3dLib.drawRotated.argtypes=[ c_double, c_double, c_double,
                                   c_double, c_double, c_double, c_double,
                                   c_double, c_double, c_double, c_double,
                                   c_void_p, c_float, c_void_p ]
object3dLib.drawRotated.restype=None

collider.updateColliders.argtypes=[ c_void_p,
                                       c_uint,
                                       c_double, c_double, c_double,
                                       c_double, c_double, c_double, c_double ]
collider.updateColliders.restype=None

collider.allocColliders.argtypes=[ c_uint ]
collider.allocColliders.restype=c_void_p

collider.allocTransCols.argtypes=[ c_void_p ]
collider.allocTransCols.restype=c_void_p

object3dLib.deleteColliders.argtypes=[ c_void_p ]
object3dLib.deleteColliders.restype=None

collider.deleteTransCols.argtypes=[ c_void_p ]
collider.deleteTransCols.restype=None

collider.loadCollider.argtypes=[ c_void_p, c_uint, c_char_p, c_float ]
collider.loadCollider.restype=None

collider.identifyBigCollider.argtypes=[ c_void_p ]
collider.identifyBigCollider.restype=None

#object3dLib.createVBO.argtypes=[ c_void_p, c_uint, c_void_p ];
#object3dLib.createVBO.restype=c_int

def updateTime():
    global now, delta, iteration
    n=time()
    delta=n-now
    now=n
    iteration+=1
    
now=time()
delta=0.0
