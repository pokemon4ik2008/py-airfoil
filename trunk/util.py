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
