from euclid import *
from pyglet.gl import *

from control import Controller

class Camera:
    def __init__(self, plane):
        self._plane=plane
        (self._xrot, self._zrot)=(0,0)

    def activate(self):
        pass

    def setPos(self, xrot, zrot):
        (self._xrot, self._zrot)=(xrot, zrot)

class FollowCam(Camera):
    def __init__(self, plane):
        Camera.__init__(self, plane)

    def activate(self):
        att = self._plane.getAttitude()
        adjAtt = Quaternion.new_rotate_euler( self._zrot/180.0*math.pi, self._xrot/180.0*math.pi, 0.0)
        cameraAjust = adjAtt * Vector3(-100.0,50.0, 2.0)
        pos = self._plane.getPos()
        eye = pos + cameraAjust
        zen = adjAtt * Vector3(0.0,1.0,0.0)
        gluLookAt(eye.x, eye.y, eye.z,
                  pos.x, pos.y, pos.z,
                  zen.x, zen.y, zen.z)

class FixedCam(Camera):
    def __init__(self, plane):
        Camera.__init__(self, plane)

    def activate(self):
        att = self._plane.getAttitude()
        adjAtt = Quaternion.new_rotate_euler( self._zrot/180.0*math.pi, self._xrot/180.0*math.pi, 0.0)
        cameraAjust = att * adjAtt * Vector3(-100.0,10.0, 2.0)
        pos = self._plane.getPos()
        eye = pos + cameraAjust
        zen = att * adjAtt * Vector3(0.0,1.0,0.0)
        gluLookAt(eye.x, eye.y, eye.z,
                  pos.x, pos.y, pos.z,
                  zen.x, zen.y, zen.z)

class View:
    __FOLLOW=0
    __FIXED=1
    def __init__(self, controller, win, plane, num_players, opt):
        self.__opt=opt
        self.__cams=[FollowCam(plane), FixedCam(plane)]
        self.__currentCamera = self.__cams[View.__FIXED]
        self.__controls = controller
        self.__plane_id=plane.getId()
        self.__win=win
        self.__num_players=num_players
        self.__updateDimensions()
        #print "view: x orig: "+str(self.__xOrig)+" y orig: "+str(self.__yOrig)+" width: "+str(self.__width)+" height: "+str(self.__height)
        (self.__xrot, self.__zrot, self.__zoom) = (0, 0, -150)
        self.__screenMessage=''
      
    def __updateDimensions(self):
        self.__width=self.__win.width
        self.__height=self.__win.height/self.__num_players
        (self.__xOrig, self.__yOrig) = (0, self.__height*(self.__num_players -1 - self.__plane_id))
        if self.__num_players==1:
            f_size=16
            width_offset=self.__win.width*0.5
        else:
            f_size=24
            width_offset=self.__win.width*0.75
        self.__label = pyglet.text.Label('bla',
                          font_name='Times New Roman',
                          font_size=f_size,
                          x= - width_offset, y=self.__win.height/2.0,
                          anchor_x='left', anchor_y='top')
        #x= - self.__win.width/2.0, y=self.__win.height/2.0,

    def getPlaneId(self):
        return self.__plane_id

    def eventCheck(self):
        interesting_events = [Controller.CAM_FIXED, 
                              Controller.CAM_FOLLOW, 
                              Controller.CAM_X,
                              Controller.CAM_Z,
                              Controller.CAM_ZOOM]
        events = self.__controls.eventCheck(interesting_events)

        if events[Controller.CAM_FOLLOW]!=0:
            self.__currentCamera = self.__cams[View.__FOLLOW]
        if events[Controller.CAM_FIXED]!=0:
            self.__currentCamera = self.__cams[View.__FIXED]
        self.__zrot += events[Controller.CAM_Z]
        self.__xrot += events[Controller.CAM_X]
        self.__zoom += events[Controller.CAM_ZOOM]
        self.__currentCamera.setPos(self.__xrot, self.__zrot)
        self.__controls.clearMouseEvents(interesting_events)

    def activate(self):
        self.__updateDimensions()
        if self.__height==0:
            height=1
        else:
            height=self.__height
        #print "view: x orig: "+str(self.__xOrig)+" y orig: "+str(self.__yOrig)+" width: "+str(self.__width)+" height: "+str(self.__height)
        glViewport(self.__xOrig, self.__yOrig, self.__width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70, 1.0*self.__width/height, 0.1, self.__opt.width * 1.2)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.__currentCamera.activate()

    def printToScreen(self, message):        
            self.__screenMessage += '[' + message + ']'

    def drawText(self):
            glPushMatrix()
            glTranslatef(-200, 0, -750)
            self.__label.color = (0, 0, 0, 255)
            self.__label.text = self.__screenMessage                
            self.__label.draw()
            glPopMatrix()
            self.__clearText()

    def __clearText(self):
        self.__screenMessage = ''
