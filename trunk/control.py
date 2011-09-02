from pyglet.window import key, mouse
from time import time
from util import repeat

class Enum:
    def __init__(self):
        pass

class Controls(Enum):
    def __init__(self, name):
        self.__name=name
        self.default_val=0

    def __str__(self):
        return self.__name

    def __repr__(self):
        return self.__name

class Action:
    def __init__(self, name):
        self.__name=name
        self._auto_clears=False

    def __str__(self):
        return self.__name

    def __repr__(self):
        return self.__name

class KeyAction(Action):
    __KEYS = key.KeyStateHandler()

    def __init__(self, k1, k2=None, mod=0, onPress=False):
        Action.__init__(self, 'KeyAction: '+str(k1)+' '+str(k2))
        self.__k1=k1
        self.__k2=k2
        self.__mod=mod
        self.__onPress=onPress

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

    def checkOnPress(self):
        return self.__onPress

    @staticmethod
    def getKeys():
        return KeyAction.__KEYS

class MouseAction(Action):
    DIMS=(X,Y,Z)=range(3)
    START_DIM=X

    def __init__(self, sensitivity, dim, accumulate=True, normalise=True):
        Action.__init__(self, 'MouseAction. sensitivity: '+str(sensitivity))
        self._sensitivity=sensitivity
        self._dim=dim
        self.__accumulate=accumulate
        self.__normalise=normalise

    def dim(self):
        if(self._dim == None):
            raise NotImplementedError
        else:
            return self._dim

    def getState(self, old, delta, period):
        this_state=(delta/float(period)) * self._sensitivity
        if self.__accumulate:
            return old + this_state
        else:
            return this_state

class MouseButAction(MouseAction):
    DIMS=(LEFT,MID,RIGHT)=range(len(MouseAction.DIMS), 6)
    START_DIM=LEFT
    __BUT_MASK={LEFT: mouse.LEFT, MID: mouse.MIDDLE, RIGHT: mouse.RIGHT}

    def __init__(self, dim):
        Action.__init__(self, 'MouseButAction: dim: '+str(dim))
        self._dim=dim
        self._auto_clears=True

    def matches(self, combined, modifiers):
        masked=MouseButAction.__BUT_MASK[self.dim()] & combined
        if masked==0:
            return False
        else:
            return True

class Controller:
    THRUST=Controls("thrust")
    PITCH=Controls("pitch")
    ROLL=Controls("roll")
    FIRE=Controls("fire")
    CAM_FIXED=Controls("fixed camera")
    CAM_FOLLOW=Controls("follow camera")
    CAM_INTERNAL=Controls("internal camera")
    CAM_X=Controls("camera x")
    CAM_Z=Controls("camera z")
    CAM_ZOOM=Controls("camera zoom")
    TOG_MOUSE_CAP =Controls("toggle mouse capture")
    TOG_SOUND_EFFECTS =Controls("toggle sound effects")
    NO_ACTION=Controls("nothing")

    __WINS = []
    __INSTANCES = []

    def __init__(self, controls, win):
	if not win in Controller.__WINS:
            @win.event
            def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
                for c in Controller.__INSTANCES:
                    c.__accum_mouse_motion(dx, dy, 0)

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
                    map(lambda (ctrl, action): c.__setMouseButtonVals(button, modifiers, (ctrl, action), 1), c.__control_types.get(MouseButAction, {}).items())

            @win.event
            def on_mouse_release(x, y, button, modifiers):
                for c in Controller.__INSTANCES:
                    map(lambda (ctrl, action): c.__setMouseButtonVals(button, modifiers, (ctrl, action), 0), c.__control_types.get(MouseButAction, {}).items())

            @win.event
            def on_key_press(symbol, mods):
                for c in Controller.__INSTANCES:
                    for ctrl in [control for control in c.__on_key_press]:
                        if c.__controls[ctrl].matches(symbol, mods):
                            c.__vals[ctrl] = 1

            win.push_handlers(KeyAction.getKeys())
            Controller.__WINS.append(win)
        Controller.__INSTANCES.append(self)
        self.__controls = dict(controls)
        self.__control_types={}
        for (k,v) in self.__controls.items():
            if v.__class__ not in self.__control_types:
                self.__control_types[v.__class__]={}
            self.__control_types[v.__class__][k]=v

        self.__controls_list = self.__controls.keys()
        print 'Controller.__init__. self: '+str(self)+' controls: '+str(self.__controls_list)
        self.__on_key_press=[control for (control, action) in self.__control_types.get(KeyAction, {}).items() if action.checkOnPress()]
        self.__on_key_press_not=[control for (control, action) in self.__control_types.get(KeyAction, {}).items() if not action.checkOnPress()]
        self.__vals=dict([ (c, c.default_val) for c in self.__controls]);
        (self.__mouse_actions, self.__last_mouse_time) = (self.__gen_actions(MouseAction), None)
        (self.__mouse_but_actions, self.__last_but_time) = (self.__gen_actions(MouseButAction), None)

    def clearEvents(self, controls=None):
        if controls is None:
            controls=self.__controls_list
        for c in controls:
            if c in self.__controls and not self.__controls[c]._auto_clears:
                self.__vals[c]=0

    def __setMouseButtonVals(self, button, modifiers, (c, a), val):
        if a.matches(button, modifiers):
            self.__vals[c] = val

    def __gen_actions(self, action_class):
        mouse_ctrls=self.__control_types.get(action_class, {})
        control_actions=repeat((Controller.NO_ACTION, None), len(action_class.DIMS))
        for (c, a) in mouse_ctrls.items():
            control_actions[a.dim()-action_class.START_DIM]=(c, a)
        return control_actions

    def __set_mouse_vals(self, action_class, actions, deltas, last_time):
        if last_time is None:
              return time()
        now=time()
        period=now-last_time
        self.__last_mouse_time=now
        
        mouse_ctrls=self.__control_types.get(action_class, {})
        self.__vals.update([ (control, mouse_ctrls[control].getState(self.__vals[control], delta, period)) 
                             for ((control, action), delta) in zip(actions, deltas) 
                             if control is not Controller.NO_ACTION ])
        return now

    def __accum_mouse_motion(self, dx, dy, dz):
        self.__last_mouse_time=self.__set_mouse_vals(MouseAction, self.__mouse_actions, [dx, dy, dz], self.__last_mouse_time)

    def eventCheck(self, interesting=None):
        if interesting is None:
            interesting=self.__controls_list
        for i in [control for control in interesting if control in self.__on_key_press_not]:
            self.__vals[i] = self.__controls[i].getState()

        return self.__vals

