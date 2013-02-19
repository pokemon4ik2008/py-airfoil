try:
        from api import getAPI, PYGLET, PYGAME
        from traceback import print_exc, print_stack
        from collections import defaultdict
        from ctypes import *
        import os
        #raise ImportError()
        import pyglet
        from pyglet import *
	if os.name == 'nt':
	    object3dLib = cdll.LoadLibrary("bin\object3d.dll")
	else:
	    object3dLib = cdll.LoadLibrary("bin/libobject3d.so")

        #api='pyglet'
        api=getAPI()
except ImportError:
        api=PYGAME
        
if api==PYGLET:
        print 'pyglet installed'
        try:
                from pyglet.gl import glu
                from pyglet.window import key
                from pyglet.window import mouse
                import mesh
                
                #global mouse
                
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
                Label=pyglet.text.Label
                sndLoad=pyglet.media.load
                appExit=pyglet.app.exit
                
                EventDispatcher=pyglet.event.EventDispatcher
                Player=pyglet.media.Player
                Window=pyglet.window.Window
                Config=pyglet.gl.Config
                
                glBegin=gl.glBegin
                glBindTexture=gl.glBindTexture
                glBlendFunc=gl.glBlendFunc
                glClear=gl.glClear
                glClearColor=gl.glClearColor
                glClearDepth=gl.glClearDepth
                glColor3f=gl.glColor3f
                glColor4f=gl.glColor4f
                glColorMaterial=gl.glColorMaterial
                glDepthFunc=gl.glDepthFunc
                glDepthMask=gl.glDepthMask
                glDisable=gl.glDisable
                glEnable=gl.glEnable
                glEnd=gl.glEnd
                glFinish=gl.glFinish
                glLightfv=gl.glLightfv
                glLoadIdentity=gl.glLoadIdentity
                glMatrixMode=gl.glMatrixMode
                glPointSize=gl.glPointSize
                glPopMatrix=gl.glPopMatrix
                glPushMatrix=gl.glPushMatrix
                glShadeModel=gl.glShadeModel
                glTexCoord2f=gl.glTexCoord2f
                glTexParameteri=gl.glTexParameteri
                glTranslatef=gl.glTranslatef
                glVertex3f=gl.glVertex3f
                glViewport=gl.glViewport
                
                GL_AMBIENT=gl.GL_AMBIENT
                GL_AMBIENT_AND_DIFFUSE=gl.GL_AMBIENT_AND_DIFFUSE
                GL_BLEND=gl.GL_BLEND
                GL_CLAMP_TO_EDGE=gl.GL_CLAMP_TO_EDGE
                GL_COLOR_BUFFER_BIT=gl.GL_COLOR_BUFFER_BIT
                GL_COLOR_MATERIAL=gl.GL_COLOR_MATERIAL
                GL_CULL_FACE=gl.GL_CULL_FACE
                GL_DEPTH_BUFFER_BIT=gl.GL_DEPTH_BUFFER_BIT
                GL_DEPTH_TEST=gl.GL_DEPTH_TEST
                GL_DIFFUSE=gl.GL_DIFFUSE
                GL_FOG=gl.GL_FOG
                GL_FRONT=gl.GL_FRONT
                GL_LEQUAL=gl.GL_LEQUAL
                GL_LIGHT0=gl.GL_LIGHT0
                GL_LIGHTING=gl.GL_LIGHTING
                GL_POINT_SMOOTH=gl.GL_POINT_SMOOTH
                GL_LINEAR=gl.GL_LINEAR
                GL_LINES=gl.GL_LINES
                GL_POINTS=gl.GL_POINTS
                GL_MODELVIEW=gl.GL_MODELVIEW
                GL_ONE_MINUS_SRC_ALPHA=gl.GL_ONE_MINUS_SRC_ALPHA
                GL_POSITION=gl.GL_POSITION
                GL_PROJECTION=gl.GL_PROJECTION
                GL_QUADS=gl.GL_QUADS
                GL_SMOOTH=gl.GL_SMOOTH
                GL_SPECULAR=gl.GL_SPECULAR
                GL_SRC_ALPHA=gl.GL_SRC_ALPHA
                GL_TEXTURE_WRAP_S=gl.GL_TEXTURE_WRAP_S
                GL_TEXTURE_WRAP_T=gl.GL_TEXTURE_WRAP_T
                GL_TEXTURE_WRAP_R=gl.GL_TEXTURE_WRAP_R
                GL_TEXTURE_MAG_FILTER=gl.GL_TEXTURE_MAG_FILTER
                GL_TEXTURE_MIN_FILTER=gl.GL_TEXTURE_MIN_FILTER
                GL_TRIANGLES=gl.GL_TRIANGLES
                
                gluPerspective=glu.gluPerspective
                gluLookAt=glu.gluLookAt
        except:
                print 'Failed to import glu. X might not be running';
else:
        import pygame
        import pygame as k
        import key
        
        print 'pygame installed'
        #global mouse
        import mouse
        from control import MouseButAction
        
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

        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        found = False
        disp_no = os.getenv("DISPLAY")
        TIMER=pygame.USEREVENT
        getEvent=None
        def initDisplay():
                size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
                print "Framebuffer size: %d x %d" % (size[0], size[1])
                screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
                
                pygame.display.init()
                pygame.display.set_mode((1,1))
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(1)
                getEvent=pygame.event.get()
        if disp_no:
                print "I'm running under X display = {0}".format(disp_no)
                initDisplay()
        else:
                # Check which frame buffer drivers are available
                # Start with fbcon since directfb hangs with composite output
                drivers = ['fbcon', 'directfb', 'svgalib']
                for driver in drivers:
                        # Make sure that SDL_VIDEODRIVER is set
                        if not os.getenv('SDL_VIDEODRIVER'):
                                os.putenv('SDL_VIDEODRIVER', driver)
                        try:
                                pygame.display.init()
                        except pygame.error as e:
                                print 'Driver: {0} failed. msg: {1}.'.format(driver, str(e))
                                continue
                        found = True
                        break
                if not found:
                        print 'No suitable video driver found! Running headless'
                        from time import sleep

                        class Event:
                                def __init__(self):
                                        self.type=TIMER+1

                        STUB_EVENT=Event()
                        def getEvent():
                                sleep(1)
                                return STUB_EVENT
                else:
                        initDisplay()

        global alive
        alive=True
        eventActions={}
        
        FRAME_INTERVAL=17
        def pygameSchedule(callback):
             eventActions[TIMER]=lambda e : callback(FRAME_INTERVAL)   
             pygame.time.set_timer(TIMER, FRAME_INTERVAL)
        schedule=pygameSchedule
        
        def pygameRun():
                print 'pygameRun. start'
                event=pygame.QUIT
                try:
                        while alive:
                                for event in getEvent():
                                        if event.type!=TIMER:
                                                print 'pygameRun. event: '+str(event)
                                        eventActions[event.type](event)
                except KeyError:
                        Window.close()
                        try:
                                assert event.type==pygame.QUIT
                        except AssertionError:
                                print 'event: '+str(event)
                                print_exc()
                print 'pygameRun. end'
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
        def appExit():
                global alive
                if alive==True:
                        print 'quitting'
                alive=False

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
                any_exit=False
                
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
                        def deMultiPlexMouseButton(event, mouseButtons):
                                (x, y)=event.pos
                                yScroll=0
                                if event.button>=len(mouseButtons):
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
                        return Window.any_exit

                @has_exit.setter
                def has_exit(self, value):
                        Window.any_exit=value
                        
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
                        print 'Window.close. setting win.any_exit.'
                        Window.any_exit=True
                
        class Config:
                def __init__(self, double_buffer, depth_size):
                        pass
                        
        glBegin=lambda prim: None
	glBindTexture=lambda target, id : None
        glBlendFunc=lambda src, action : None
        glClear=lambda buf : None
	glClearColor=lambda r, g, b, a: None
	glClearDepth=lambda val: None
	glColor3f=lambda r, g, b: None
	glColor4f=lambda r, g, b, a : None
	glColorMaterial=lambda side, lighting: None
        glDepthFunc=lambda f : None
	glDepthMask=lambda enable : None
	glDisable=lambda flag: None
	glEnable=lambda flags : None
	glEnd=lambda : None
        glFinish=lambda : None
        glLightfv=lambda source, ligthing, val: None
	glLoadIdentity=lambda : None
	glMatrixMode=lambda mode : None
        glPointSize=lambda size : None
	glPopMatrix=lambda : None
	glPushMatrix=lambda : None
        glShadeModel=lambda shader : None
	glTexCoord2f=lambda x, y : None
	glTexParameteri=lambda target, flags, map_flags : None
	glTranslatef=lambda x, y, z : None
	glVertex3f=lambda x, y, z: None
        glViewport=lambda xOrig, yOrig, width, height: None 

        GL_AMBIENT=0
        GL_AMBIENT_AND_DIFFUSE=0
        GL_BLEND=0
	GL_CLAMP_TO_EDGE=0
        GL_COLOR_BUFFER_BIT=0
        GL_COLOR_MATERIAL=0
	GL_CULL_FACE=0
        GL_DEPTH_BUFFER_BIT=0
	GL_DEPTH_TEST=0
        GL_DIFFUSE=0
        GL_FOG=0
        GL_FRONT=0
        GL_LEQUAL=0
        GL_LIGHT0=0
	GL_LINEAR=0
	GL_LINES=0
	GL_LIGHTING=0
        GL_POINTS=0
        GL_POINT_SMOOTH=0
	GL_MODELVIEW=0
        GL_ONE_MINUS_SRC_ALPHA=0
        GL_POSITION=0
        GL_PROJECTION=0
	GL_QUADS=0
        GL_SMOOTH=0
        GL_SPECULAR=0
        GL_SRC_ALPHA=0
	GL_TEXTURE_MAG_FILTER=0
	GL_TEXTURE_MIN_FILTER=0
	GL_TEXTURE_WRAP_R=0
	GL_TEXTURE_WRAP_S=0
	GL_TEXTURE_WRAP_T=0
	GL_TRIANGLES=0

	gluPerspective=lambda fov_y, aspect, z_near, z_far : None
        gluLookAt=lambda eyeX, eyeY, eyeZ, posX, posY, posZ, zenX, zenY, zenZ: None
