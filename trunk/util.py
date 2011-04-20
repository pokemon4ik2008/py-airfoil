import math
 
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
