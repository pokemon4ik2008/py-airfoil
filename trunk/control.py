from pyglet.window import key

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

    def __init__(self, k1, k2=None):
        Action.__init__(self, 'KeyAction: '+str(k1)+' '+str(k2))
        self.__k1=k1
        self.__k2=k2

    def getState(self):
        if KeyAction.__KEYS[self.__k1]:
            return 1
        if self.__k2 is not None and KeyAction.__KEYS[self.__k2]:
            return -1
        return 0

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
                    #print "on_mouse_motion: x "+str(x)+" y "+str(y)+" dx "+str(dx)+" dy "+str(dy)
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

            win.push_handlers(KeyAction.getKeys())
        Controller.__WINS.append(win)
        Controller.__INSTANCES.append(self)
        self.__controls = dict(controls)
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
                          (Controller.NO_ACTION, 0)]);
        self.__first_mouse_motion = True

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

    def clearMouseEvents(self, controls):
        for c in controls:
            if(c in self.__mouse_controls):
                self.__vals[c]=0

    def __accum_mouse_motion(self, dx, dy, dz):
        #print "accum_mouse_motion: "+str(dx)+" "+str(dy)+" "+str(dz)
        if self.__first_mouse_motion:
            # first dx or dy seems to be an offsset from the window origin
            # this is too large so we ignore it
            self.__first_mouse_motion = False
            return

        self.__vals.update([(action, self.__vals[action] + self.__controls[action].getState(delta)) 
                            for (action, delta) in zip(self.__mouse_controls, [dx, dy, dz]) 
                            if action != Controller.NO_ACTION])

    def eventCheck(self, interested):
        for i in [control for control in interested if control in self.__key]:
            self.__vals[i] = self.__controls[i].getState()

        return self.__vals

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
        else:
            ratio = self.getElevatorRatio()
            if ratio > 0.0:
                self.adjustPitch(-0.01)
            elif ratio < 0.0:
                self.adjustPitch(0.01)
        
        rollAdjust = 0.01
        if events[Controller.ROLL]!=0:
            self.adjustRoll(-events[Controller.ROLL]*rollAdjust)
        else:
            ratio = self.getAileronRatio()
            if ratio > 0.0:
                self.adjustRoll(-0.01)
            elif ratio < 0.0:
                self.adjustRoll(0.01)

        self.__controls.clearMouseEvents(interesting_events)
