try:
        from traceback import print_exc, print_stack
        from collections import defaultdict
        from ctypes import *
        from pyglet import *
        from pyglet.gl import glu
        import os

        raise ImportError()
        import pyglet
        from pyglet import gl
        from pyglet import window, font, clock # for pyglet 1.0
	import mesh

	if os.name == 'nt':
	    object3dLib = cdll.LoadLibrary("bin\object3d.dll")
	else:
	    object3dLib = cdll.LoadLibrary("bin/libobject3d.so")

        api='pyglet'
except ImportError:
        import pygame
        import pygame as k
        import key
        
        api='pygame'

if api=='pyglet':
        print 'pyglet installed'
        from pyglet.window import key
        from pyglet.window import mouse

        schedule=pyglet.clock.schedule
        run=pyglet.app.run
	setLightPosition=object3dLib.setLightPosition
	drawVBO=object3dLib.drawVBO
	#load=object3dLib.load

        object3dLib.createVBO.argtypes=[ c_void_p, c_uint, c_void_p ];
        object3dLib.createVBO.restype=c_int
	createVBO=object3dLib.createVBO

        deleteVBO=object3dLib.deleteVBO

        object3dLib.deleteMesh.argtypes=[ c_void_p ]
        object3dLib.deleteMesh.restype=None
	deleteMesh=object3dLib.deleteMesh

        #object3dLib.getMeshPath.argtypes=[ c_void_p ]
        #object3dLib.getMeshPath.restype=c_char_p
	#getMeshPath=object3dLib.getMeshPath

        object3dLib.getUvPath.argtypes=[ c_void_p, c_uint ]
        object3dLib.getUvPath.restype=c_char_p
	getUvPath=object3dLib.getUvPath

        object3dLib.setupTex.argtypes=[ c_void_p, c_uint, c_uint ]
        object3dLib.setupTex.restype=c_uint
	setupTex=object3dLib.setupTex
	getMid=object3dLib.getMid

        object3dLib.setupRotation.argtypes=[ c_double, c_double, c_double,
                                             c_double, c_double, c_double, c_double,
                                             c_double, c_double, c_double,
                                             c_double, c_double, c_double ]
        object3dLib.setupRotation.restype=None
	setupRotation=object3dLib.setupRotation

        object3dLib.drawToTex.argtypes=[ c_void_p, c_float, c_uint, c_uint, c_uint, c_uint, c_uint, c_uint ]
        object3dLib.drawToTex.restype=None
	drawToTex=object3dLib.drawToTex

        object3dLib.draw.argtypes=[ c_void_p, c_float ]
        object3dLib.draw.restype=None
	draw=object3dLib.draw

        object3dLib.drawRotated.argtypes=[ c_double, c_double, c_double,
                                   c_double, c_double, c_double, c_double,
                                   c_double, c_double, c_double, c_double,
                                   c_void_p, c_float, c_void_p ]
        object3dLib.drawRotated.restype=None
        drawRotated=object3dLib.drawRotated

        object3dLib.createTexture.argtypes=[ c_void_p, c_uint, c_void_p, c_uint, c_uint, c_uint ]
        object3dLib.createTexture.restype=c_uint
        createTexture=object3dLib.createTexture

        object3dLib.createFBO.argtypes=[ c_uint, c_uint, c_uint ]
        object3dLib.createFBO.restype=c_uint
        createFBO=object3dLib.createFBO
        setAngleAxisRotation=object3dLib.setAngleAxisRotation
        listener=media.listener
	imageLoad=image.load
	sndLoad=pyglet.media.load

	EventDispatcher=pyglet.event.EventDispatcher
	Label=pyglet.text.Label
	Player=pyglet.media.Player
        Window=pyglet.window.Window
        
	glBegin=gl.glBegin
	glBindTexture=gl.glBindTexture
	glColor3f=gl.glColor3f
	glColor4f=gl.glColor4f
	glDepthMask=gl.glDepthMask
	glDisable=gl.glDisable
	glEnable=gl.glEnable
	glEnd=gl.glEnd
	glLoadIdentity=gl.glLoadIdentity
        glViewport=gl.glViewport
	glMatrixMode=gl.glMatrixMode
	glPopMatrix=gl.glPopMatrix
	glPushMatrix=gl.glPushMatrix
	glTexCoord2f=gl.glTexCoord2f
	glTexParameteri=gl.glTexParameteri
	glTranslatef=gl.glTranslatef
	glVertex3f=gl.glVertex3f

	GL_CLAMP_TO_EDGE=gl.GL_CLAMP_TO_EDGE
	GL_CULL_FACE=gl.GL_CULL_FACE
	GL_DEPTH_TEST=gl.GL_DEPTH_TEST
	GL_FOG=gl.GL_FOG
	GL_LIGHTING=gl.GL_LIGHTING
	GL_LINEAR=gl.GL_LINEAR
	GL_LINES=gl.GL_LINES
	GL_MODELVIEW=gl.GL_MODELVIEW
	GL_PROJECTION=gl.GL_PROJECTION
	GL_QUADS=gl.GL_QUADS
	GL_TEXTURE_WRAP_S=gl.GL_TEXTURE_WRAP_S
	GL_TEXTURE_WRAP_T=gl.GL_TEXTURE_WRAP_T
	GL_TEXTURE_WRAP_R=gl.GL_TEXTURE_WRAP_R
	GL_TEXTURE_MAG_FILTER=gl.GL_TEXTURE_MAG_FILTER
	GL_TEXTURE_MIN_FILTER=gl.GL_TEXTURE_MIN_FILTER
	GL_TRIANGLES=gl.GL_TRIANGLES

	gluPerspective=glu.gluPerspective
        gluLookAt=glu.gluLookAt
else:
        print 'pygame installed'
        import mouse
        
        pygame2PygletKeyList=[
                (k.K_a, key.A),
                (k.K_c, key.C),
                (k.K_d, key.D),
                (k.K_e, key.E),
                (k.K_f, key.F),
                (k.K_h, key.H),
                (k.K_j, key.J),
                (k.K_k, key.K),
                (k.K_m, key.M),
                (k.K_n, key.N),
                (k.K_o, key.O),
                (k.K_p, key.P),
                (k.K_q, key.Q),
                (k.K_r, key.R),
                (k.K_s, key.S),
                (k.K_v, key.V),
                (k.K_w, key.W),
                (k.K_x, key.X),
                (k.K_z, key.Z),
                (k.K_0, key._0),
                (k.K_1, key._1),
                (k.K_2, key._2),
                (k.K_3, key._3),
                (k.K_8, key._8),
                (k.K_9, key._9),
                (k.K_ESCAPE, key.ESCAPE),
                (k.K_PAGEDOWN, key.PAGEDOWN),
                (k.K_PAGEUP, key.PAGEUP),
                ]

        # app=QtGui.QApplication(sys.argv)
        # pygame.init()
        pygame.display.init()
        pygame.display.set_mode((1,1))
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(1)

        QUITTING=False
        eventActions={}
        TIMER=pygame.USEREVENT
        
        FRAME_INTERVAL=17
        def pygameSchedule(callback):
             eventActions[TIMER]=lambda e : callback(FRAME_INTERVAL)   
             pygame.time.set_timer(TIMER, FRAME_INTERVAL)
        schedule=pygameSchedule

        def pygameRun():
                event=pygame.QUIT
                try:
                        while True:
                                for event in pygame.event.get():
                                        if event.type!=pygame.USEREVENT:
                                                print 'pygameRun. event: '+str(event)
                                        eventActions[event.type](event)
                except KeyError:
                        Window.close()
                        try:
                                assert event.type==pygame.QUIT
                        except AssertionError:
                                print 'event: '+str(event)
                                print_exc()
                return
        run=pygameRun
        
                
	setLightPosition = lambda lightPos : None
	drawVBO=lambda v: None
	#load=lambda path, scale, group: None
	createVBO=lambda group: None
	deleteVBO=lambda vbo: None
	deleteMesh=lambda mesh: None
        #getMeshPath=lambda mesh: ''
	getUvPath=lambda mesh, uvId: None
	setupTex=lambda mesh, uvId, texId: None
	getMid=lambda centre_mesh, mid: None
	setupRotation=lambda x, y, z, wr, xr, yr, zr, xmid, ymid, zmid, xorig, yorig, zorig: None
	drawToTex=lambda mesh, alpha, fbo, width, height, bg, boundPlane, top: None
	draw=lambda mesh, alpha: None
	drawRotated=lambda xPos, yPos, zPos, wAtt, xAtt, yAtt, zAtt, wAng, xAng, yAng, zAng, p_centre_mesh, alpha, p_mesh: None
        createTexture=lambda mesh, uv_id, data, width, height, form: 0
        createFBO=lambda texId, width, height: 0
        class Listener:
                def __init__(self):
                        pass
        listener=Listener()
        setAngleAxisRotation=lambda angle, fpos: None
        class Texture():
                def __init__(self):
                        self.id=0
                        self.target=0
                        self.tex_coords=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
                                         0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

                def get_texture(self):
                        return self
                        
        class Image:
                def get_texture(self):
                        return Texture()
                        
	imageLoad=lambda path: Image()
	sndLoad=lambda path, streaming : None

	class EventDispatcher:
                def event(self, *args):
                        return args[0]

                def push_handlers(self, *args, **kwargs):
                        pass
                        
                @classmethod
                def register_event_type(cls, ev):
                        pass

	class Label:
		def __init__(self, txt, font_name, font_size, x, y, anchor_x, anchor_y):
			self.color=(0, 0, 0, 0)
			self.text=''

		def draw(self):
			pass

	class Player(EventDispatcher):
		EOS_LOOP=0
		EOS_PAUSE=1

		def __init__(self):
			self.volume=0.0
			self.pitch=0.0
			self.playing=False
			self.position=(0.0, 0.0, 0.0)
			self.eos_action='stop'
			self.min_distance=0

		def next(self):
			pass

		def pause(self):
			pass

		def play(self):
			pass

		def queue(self, snd):
			pass

        class Window(EventDispatcher):
                has_exit=False
                
                def __init__(self, config, width, height, resizable, fullscreen=False):
                        print 'Window.__init__. start'
                        self.width=1
                        self.height=1
                        
                        def parseMotionEvent(event):
                                (x, y)=event.pos
                                (dx, dy)=event.rel
                                return (x, y, dx, dy)
                        eventActions[pygame.ACTIVEEVENT]=lambda event: None
                        eventActions[pygame.VIDEORESIZE]=lambda event: None
                        eventActions[pygame.MOUSEMOTION]=lambda event: self.on_mouse_motion(*parseMotionEvent(event))
                        mousePressButtons=[None, 
                                      lambda x, y, mods: self.on_mouse_press(x, y, MouseButAction.LEFT, mods), 
                                      lambda x, y, mods: self.on_mouse_press(x, y, MouseButAction.MID, mods), 
                                      lambda x, y, mods: self.on_mouse_press(x, y, MouseButAction.RIGHT, mods), 
                                      lambda x, y, mods: self.on_mouse_scroll(x, y, 0, -1),
                                      lambda x, y, mods: self.on_mouse_scroll(x, y, 0, 1)]
                        mouseReleaseButtons=[None, 
                                      lambda x, y, mods: self.on_mouse_release(x, y, MouseButAction.LEFT, mods), 
                                      lambda x, y, mods: self.on_mouse_release(x, y, MouseButAction.MID, mods), 
                                      lambda x, y, mods: self.on_mouse_release(x, y, MouseButAction.RIGHT, mods), 
                                      ]
                        def deMultiPlexMouseButtonPress(event, mouseButtons):
                                (x, y)=event.pos
                                yScroll=0
                                if event.button>=len(mousePressButtons):
                                        return
                                mouseButtons[event.button](x, y, 0)
                        eventActions[pygame.MOUSEBUTTONDOWN]=lambda event: deMultiPlexMouseButton(event, mousePressButtons)
                        eventActions[pygame.MOUSEBUTTONUP]=lambda event: deMultiPlexMouseButton(event, mouseReleaseButtons)

                        pygame2PygletKey=defaultdict(lambda : (lambda arg1, arg2: None))
                        for (pygame_key, pyglet_key) in pygame2PygletKeyList:
                                pygame2PygletKey[pygame_key]=lambda f, mod: f(pyglet_key, mod)
                        pygame2PygletKey[k.K_ESCAPE]=lambda f, mod: self.finish()
                                
                        eventActions[pygame.KEYDOWN]=lambda event: (pygame2PygletKey[event.key](self.on_key_press, event.mod))
                        eventActions[pygame.KEYUP]=lambda event: (pygame2PygletKey[event.key](self.on_key_release, event.mod))

                @property
                def has_exit(self):
                        return Window.has_exit

                @has_exit.setter
                def has_exit(self, value):
                        Window.has_exit=value
                        
                def finish(self):
                        print 'finish. calling Window.close'
                        Window.close()
                        
                def on_mouse_motion(self, x, y, dx, dy):
                     pass
                
                def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
                     pass

                def on_mouse_press(self, x, y, button, modifiers):
                     pass
                     
                def on_mouse_release(self, x, y, button, modifiers):
                     pass
                     
                def on_key_press(self, symbol, mods):
                     pass

                def on_key_release(self, symbol, mods):
                     pass

                def set_vsync(self, vsync):
                        pass

                def set_exclusive_mouse(self, mouse):
                        pass
                        
                @classmethod
                def close(cls):
                        print 'Window.close. setting win.has_exit.'
                        Window.has_exit=True
                
	glBegin=lambda prim: None
	glBindTexture=lambda target, id : None
	glColor3f=lambda r, g, b: None
	glColor4f=lambda r, g, b, a : None
	glDepthMask=lambda enable : None
	glDisable=lambda flag: None
	glEnable=lambda flags : None
	glEnd=lambda : None
	glLoadIdentity=lambda : None
        glViewport=lambda xOrig, yOrig, width, height: None 
	glMatrixMode=lambda mode : None
	glPopMatrix=lambda : None
	glPushMatrix=lambda : None
	glTexCoord2f=lambda x, y : None
	glTexParameteri=lambda target, flags, map_flags : None
	glTranslatef=lambda x, y, z : None
	glVertex3f=lambda x, y, z: None
	
	GL_CLAMP_TO_EDGE=0
	GL_CULL_FACE=0
	GL_DEPTH_TEST=0
	GL_FOG=0
	GL_LINEAR=0
	GL_LINES=0
	GL_LIGHTING=0
	GL_MODELVIEW=gl.GL_MODELVIEW
	GL_PROJECTION=0
	GL_QUADS=0
	GL_TEXTURE_MAG_FILTER=0
	GL_TEXTURE_MIN_FILTER=0
	GL_TEXTURE_WRAP_R=0
	GL_TEXTURE_WRAP_S=0
	GL_TEXTURE_WRAP_T=0
	GL_TRIANGLES=0

	gluPerspective=lambda fov_y, aspect, z_near, z_far : None
        gluLookAt=lambda eyeX, eyeY, eyeZ, posX, posY, posZ, zenX, zenY, zenZ: None
