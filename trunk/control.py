from airfoil import Airfoil

class Enum:
    def __init__(self):
        pass

class Controls(Enum):
    def __init__(self, name):
        self.__name=name

class KeyMap:
    THRUST_UP=Controls("thrust up")
    THRUST_DOWN=Controls("thrust down")
    PITCH_UP=Controls("pitch up")
    PITCH_DOWN=Controls("pitch down")
    ROLL_RIGHT=Controls("roll right")
    ROLL_LEFT=Controls("roll left")

class MyAirfoil(Airfoil):
    def __init__(self, keys, key_map):
        Airfoil.__init__(self)
        self.__keys=keys
        self.__key_map=key_map

    def eventCheck(self):
        # Handle key presses
        thrustAdjust = 100
        if self.__keys[self.__key_map[KeyMap.THRUST_UP]]:
            self.changeThrust(thrustAdjust)
        if self.__keys[self.__key_map[KeyMap.THRUST_DOWN]]:
            self.changeThrust(-thrustAdjust)

        if self.__keys[self.__key_map[KeyMap.PITCH_UP]]:
            self.adjustPitch(0.01)
        elif self.__keys[self.__key_map[KeyMap.PITCH_DOWN]]:
            self.adjustPitch(-0.01)
        else:
            ratio = self.getElevatorRatio()
            if ratio > 0.0:
                self.adjustPitch(-0.01)
            elif ratio < 0.0:
                self.adjustPitch(0.01)
                        
        if self.__keys[self.__key_map[KeyMap.ROLL_RIGHT]]:
            self.adjustRoll(0.01)
        elif self.__keys[self.__key_map[KeyMap.ROLL_LEFT]]:
            self.adjustRoll(-0.01)
        else:
            ratio = self.getAileronRatio()
            if ratio > 0.0:
                self.adjustRoll(-0.01)
            elif ratio < 0.0:
                self.adjustRoll(0.01)
