from __future__ import division

from euclid import Quaternion, Vector3
import glob
import math
import os
import socket

QUART_PI=0.25*math.pi
HALF_PI=0.5*math.pi
PI2=2*math.pi

X_UNIT=Vector3(1.0, 0.0, 0.0)
Y_UNIT=Vector3(0.0, 1.0, 0.0)
NEG_Y_UNIT=-Y_UNIT
Z_UNIT=Vector3(0.0, 0.0, 1.0)
NULL_VEC=Vector3(0.0,0.0,0.0)
NULL_ROT=Quaternion.new_rotate_axis(0.0, Y_UNIT)

def testAllAngleForXY():
        testAngleForXY(57735, 100000, 1.0/6)
        testAngleForXY(1732, 1000, 1.0/3)
        testAngleForXY(1732, -1000, 4.0/6)
        testAngleForXY(57735, -100000, 5.0/6)
        testAngleForXY(0,1,2.0)
        testAngleForXY(1,0,1.0/2)
        testAngleForXY(0,-1,1.0)
        testAngleForXY(-57735, -100000, 7.0/6)
        testAngleForXY(-1732, -1000, 4.0/3)
        testAngleForXY(-1732, 1000, 5.0/3)
        testAngleForXY(-57735, 100000, 11.0/6)
        testAngleForXY(-1,0,3.0/2)

def testAngleForXY(x,y,correct):
        result=getAngleForXY(x,y)
        if abs((result/math.pi)-correct)<1.0/36:
                print '%(x)04f, %(y)04f, ok' % {'x': x, 'y': y}
        else:
                print '%(x)04f, %(y)04f, returned %(result)04f correct %(correct)04f' % { 'x': x, 'y': y, 'result': (result/math.pi), 'correct': correct }
        
def getAngleForXY(x, y):
        angle = 0.0
        if x == 0:
            angle = 0.0
        else:
            angle = HALF_PI - math.atan(math.fabs(y/x))
        if x <= 0.0 and y >= 0.0:
            angle = PI2 - angle
        elif x <= 0.0 and y < 0.0:
            angle = math.pi + angle
        elif x > 0.0 and y < 0.0:
            angle = math.pi - angle
        return angle      

def limitToMaxValue(input, max):
    if input > max:
        return max
    elif input < -max:
        return -max
    else:
        return input

global prettyfloat
class prettyfloat(float):
    def __repr__(self):
        return "%0.2f" % self

def repeat(el, num): 
    return [ el for idx in range(num) ]

def getLocalIP():
    addr = socket.gethostbyname(socket.gethostname())
    if addr.startswith('127'):
        try:
            import commands
            return commands.getoutput("hostname -I").split('\n')[0].strip()     
        except:
            print_exc()
    return addr
        
def int2Bytes(i, size):
    s=''
    for idx in range(size):
        s+=chr((i >> (idx*8)) & 0xff)
    return s

def bytes2Int(s):
    i=0
    for idx in range(len(s)):
       i |= ord(s[idx]) << (idx*8) 
    return i

def toHexStr(string):
    bytes=''
    for c in string:
        bytes+='%02x'%ord(c)
    return bytes

def getEffectiveAngle(angle):
    return angle-math.floor(angle/math.pi/2)*math.pi*2

def median3(l):
    median=maximum=minimum=l
    for v in l[1:]:
        if v>maximum:
            median=maximum
            maximum=v
        else:
            if v<minimum:
                median=minimum
                minimum=v
            else:
                median=v
    return median
                
if os.name == 'nt':
    getNativePath=lambda s: re.sub(r'/', r'\\', s)
else:
    getNativePath=lambda s: s
    
