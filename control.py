from pyglet.window import key
from time import time

from airfoil import Airfoil

class Enum:
    def __init__(self):
        pass

class Controls(Enum):
    def __init__(self, name):
        self.__name=name

    def __str__(self):
        return self.__name

class Action:
    def __init__(self, name):
        self.__name=name

    def __str__(self):
        return self.__name

class KeyAction(Action):
    __KEYS = key.KeyStateHandler()

    def __init__(self, k1, k2=None, mod=0, onRelease=False):
        Action.__init__(self, 'KeyAction: '+str(k1)+' '+str(k2))
        self.__k1=k1
        self.__k2=k2
        self.__mod=mod
        self.__onRelease=onRelease

    def getState(self):
        if KeyAction.__KEYS[self.__k1]:
            return 1
        if self.__k2 is not None and KeyAction.__KEYS[self.__k2]:
            return -1
        return 0

    def matches(self, symbol, modifier):
        if self.__k1==symbol and self.__mod==modifier:
            return True
        if self.__k2!=None and self.__k2==symbol and self.__mod==modifier:
            return True
        return False

    def checkOnRelease(self):
        return self.__onRelease

    @staticmethod
    def getKeys():
        return KeyAction.__KEYS

class MouseAction(Action):
    X=0
    Y=1
    Z=2

    def __init__(self, sensitivity):
        Action.__init__(self, 'MouseAction. sensitivity: '+str(sensitivity))
        self._sensitivity=sensitivity
        self._dim=None

    def dim(self):
        if(self._dim == None):
            raise NotImplementedError
        else:
            return self._dim

    def setDim(self, d):
        self._dim=d
        return self

    def getState(self, delta):
        return delta * self._sensitivity

class Controller:
    THRUST=Controls("thrust")
    PITCH=Controls("pitch")
    ROLL=Controls("roll")
    CAM_FIXED=Controls("fixed camera")
    CAM_FOLLOW=Controls("follow camera")
    CAM_X=Controls("camera x")
    CAM_Z=Controls("camera z")
    CAM_ZOOM=Controls("camera zoom")
    TOG_MOUSE_CAP =Controls("toggle mouse capture")
    NO_ACTION=Controls("nothing")

    __WINS = []
    __INSTANCES = []

    def __init__(self, controls, win):
	if not win in Controller.__WINS:
            @win.event
            def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
                for c in Controller.__INSTANCES:
                    c.__accum_mouse_motion(dx, dy, 0)
                #self.__set_mouse_button(buttons)

            @win.event
            def on_mouse_motion(x, y, dx, dy):
                for c in Controller.__INSTANCES:
                    c.__accum_mouse_motion(dx, dy, 0)

            @win.event
            def on_mouse_scroll(x, y, scroll_x, scroll_y):
                for c in Controller.__INSTANCES:
                    c.__accum_mouse_motion(0, 0, scroll_y)

            @win.event
            def on_mouse_press(x, y, button, modifiers):
                for c in Controller.__INSTANCES:
                #c.__set_mouse_button(buttons)
                    pass

            @win.event
            def on_key_release(symbol, mods):
                for c in [control for control in self.__key if self.__controls[control].checkOnRelease()]:
                    if self.__controls[c].matches(symbol, mods):
                        self.__vals[c] = 1

            win.push_handlers(KeyAction.getKeys())
            Controller.__WINS.append(win)
        Controller.__INSTANCES.append(self)
        self.__controls = dict(controls)
        self.__controls_list = self.__controls.keys()
        self.__key = [ key for (key, val) in controls if isinstance(val, KeyAction) ]
        self.__mouse_controls = self.setMouseActions()
        self.__vals=dict([(Controller.THRUST, 0), 
                          (Controller.PITCH, 0),
                          (Controller.ROLL, 0),
                          (Controller.CAM_Z, 0),
                          (Controller.CAM_X, 0),
                          (Controller.CAM_ZOOM, 0),
                          (Controller.CAM_FIXED, 0),
                          (Controller.CAM_FOLLOW, 0),
                          (Controller.TOG_MOUSE_CAP, 0),
                          (Controller.NO_ACTION, 0)]);
        self.__last_mouse_time = None

    def setMouseActions(self):
        mouse_controls=[Controller.NO_ACTION, Controller.NO_ACTION, Controller.NO_ACTION]
        try:
            for (control, action) in self.__controls.items():
                if isinstance(action, MouseAction):
                    assert action.dim() < len(mouse_controls)
                    mouse_controls[action.dim()]=control
        except AssertionError:
            print >> sys.stderr, 'size of dim too big for: '+str(action)
        return mouse_controls

    def clearEvents(self, controls):
        for c in controls:
            self.__vals[c]=0

    def __accum_mouse_motion(self, dx, dy, dz):
        if self.__last_mouse_time is None:
            # first dx or dy seems to be an offsset from the window origin
            # this is too large so we ignore it
            self.__last_mouse_time = time()
            return

        now=time()
        period=now-self.__last_mouse_time
        self.__last_mouse_time=now
        self.__vals.update([(action, self.__vals[action] + 
                             self.__controls[action].getState(delta/float(period))) 
                            for (action, delta) in zip(self.__mouse_controls, [dx, dy, dz]) 
                            if action != Controller.NO_ACTION])

    def eventCheck(self, interested):
        for i in [control for control in interested if control in self.__key 
                  and not self.__controls[control].checkOnRelease()]:
            self.__vals[i] = self.__controls[i].getState()

        return self.__vals

    def getControls(self):
        return self.__controls_list

class MyAirfoil(Airfoil):
    def __init__(self, pos, attitude, controls):
        Airfoil.__init__(self, pos, attitude)
        self.__controls=controls

    def eventCheck(self):
        interesting_events = [Controller.THRUST, Controller.PITCH, Controller.ROLL]
        events = self.__controls.eventCheck(interesting_events)

        thrustAdjust = 100
        self.changeThrust(events[Controller.THRUST]*thrustAdjust)
        
        pitchAdjust = 0.01
        if events[Controller.PITCH]!=0:
            self.adjustPitch(events[Controller.PITCH]*pitchAdjust)
        
        rollAdjust = 0.01
        if events[Controller.ROLL]!=0:
            self.adjustRoll(-events[Controller.ROLL]*rollAdjust)

        self.__controls.clearEvents(interesting_events)
