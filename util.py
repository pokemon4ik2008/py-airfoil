from euclid import Vector3
import math
import socket
 
X_UNIT=Vector3(1.0, 0.0, 0.0)
Y_UNIT=Vector3(0.0, 1.0, 0.0)
Z_UNIT=Vector3(0.0, 0.0, 1.0)

def getAngleForXY(x, y):
    angle = 0.0
    if x == 0:
        angle = math.pi / 2
    else:
        angle = math.atan(math.fabs(y/x))
    if x <= 0.0 and y >= 0.0:
        angle = math.pi - angle
    elif x <= 0.0 and y < 0.0:
        angle = math.pi + angle
    elif x > 0.0 and y < 0.0:
        angle = math.pi * 2 - angle
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
