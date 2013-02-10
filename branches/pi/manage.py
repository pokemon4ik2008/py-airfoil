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
global cterrain
global collider
if os.name == 'nt':
    cterrain = cdll.LoadLibrary("bin\cterrain.dll")
    collider = cdll.LoadLibrary("bin\libcollider.dll")
else:
    cterrain = cdll.LoadLibrary("bin/libcterrain.so")
    collider = cdll.LoadLibrary("bin/libcollider.so")

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
