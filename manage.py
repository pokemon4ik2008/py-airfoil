import os
from ctypes import *

from async import Scheduler

global worker
worker=Scheduler(block=False)
global proxy
proxy=None
global server
server=None
global sound_effects
sound_effects=False
global opt
global vbo
vbo=False
from time import time
global now, delta, iteration
iteration=0
global lookup_colliders
global cterrain
global collider
if os.name == 'nt':
    cterrain = cdll.LoadLibrary("bin\cterrain.dll")
    collider = cdll.LoadLibrary("bin\collider.dll")
    positions = cdll.LoadLibrary("bin\positions.dll")
else:
    cterrain = cdll.LoadLibrary("bin/libcterrain.so")
    collider = cdll.LoadLibrary("bin/libcollider.so")
    positions = cdll.LoadLibrary("bin/libpositions.so")

class Quat(Structure):
    _fields_ = [ ("w", c_float),
                 ("x", c_float),
                 ("y", c_float),
                 ("z", c_float) ]

QuatPtr=POINTER(Quat)
    
positions.newObj.argtypes=[ ]
positions.newObj.restype=c_void_p

positions.updateCorrection.argtypes=[ c_void_p, c_void_p, c_float ]
positions.updateCorrection.restype=None

positions.getCorrection.argtypes=[ c_void_p, c_float ]
positions.getCorrection.restype=QuatPtr

positions.delObj.argtypes=[ c_void_p ]
positions.delObj.restype=None

cterrain.checkCollision.argtypes=[ c_void_p, c_void_p, POINTER(c_uint) ]
cterrain.checkCollision.restype=c_bool

collider.checkCollisionCol.argtypes=[ c_void_p, c_void_p,
                                         c_void_p, POINTER(c_uint),
                                         c_void_p, POINTER(c_uint)]
collider.checkCollisionCol.restype=c_bool

collider.checkCollisionPoint.argtypes=[ c_void_p,
                                           c_double, c_double, c_double,
                                           c_double, c_double, c_double,
                                           c_void_p, POINTER(c_uint) ]
collider.checkCollisionPoint.restype=c_bool

collider.allocTransCols.argtypes=[ c_void_p ]
collider.allocTransCols.restype=c_void_p

collider.load.argtypes=[ c_char_p, c_float, c_uint ]
collider.load.restype=c_void_p

collider.updateColliders.argtypes=[ c_void_p,
                                       c_uint,
                                       c_double, c_double, c_double,
                                       c_double, c_double, c_double, c_double ]
collider.updateColliders.restype=None

collider.allocColliders.argtypes=[ c_uint ]
collider.allocColliders.restype=c_void_p

collider.allocTransCols.argtypes=[ c_void_p ]
collider.allocTransCols.restype=c_void_p

collider.deleteColliders.argtypes=[ c_void_p ]
collider.deleteColliders.restype=None

collider.deleteTransCols.argtypes=[ c_void_p ]
collider.deleteTransCols.restype=None

collider.loadCollider.argtypes=[ c_void_p, c_uint, c_char_p, c_float ]
collider.loadCollider.restype=None

collider.identifyBigCollider.argtypes=[ c_void_p ]
collider.identifyBigCollider.restype=None

collider.getMeshPath.argtypes=[ c_void_p ]
collider.getMeshPath.restype=c_char_p

def updateTime():
    global now, delta, iteration
    n=time()
    delta=n-now
    now=n
    iteration+=1
    
now=time()
delta=0.0
