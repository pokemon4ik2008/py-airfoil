try:
        import pyglet
        from pyglet import gl
        from pyglet import window, font, clock # for pyglet 1.0
        from pyglet.window import key
	import mesh
	if os.name == 'nt':
	    object3dLib = cdll.LoadLibrary("bin\object3d.dll")
	else:
	    object3dLib = cdll.LoadLibrary("bin/libobject3d.so")

        api='pyglet'
except ImportError:
        from PySide import QtCore, QtGui
        api='pyside'

if api=='pyglet':
        print 'pyglet installed'
        schedule=pyglet.clock.schedule
        run=pyglet.app.run
	setLightPosition=object3dLib.setLightPosition
	drawVBO=object3dLib.drawVBO
	load=object3dLib.load
	createVBO=object3dLib.createVBO
	deleteVBO=object3dLib.deleteVBO
	deleteMesh=object3dLib.deleteMesh
	getMeshPath=object3dLib.getMeshPath
	getUvPath=object3dLib.getUvPath
	setupTex=object3dLib.setupTex
	getMid=object3dLib.getMid
	setupRotation=object3dLib.setupRotation
	drawToTex=object3dLib.drawToTex
	draw=object3dLib.draw
	drawRotated=object3dLib.drawRotated
	imageLoad=image.load
	glPushMatrix=gl.glPushMatrix
	glPopMatrix=gl.PopMatrix
	glLoadIdentity=gl.glLoadIdentity
	glDisable=gl.glDisable
	glBegin=gl.glBegin
else:
        print 'qt installed'
        app=QtGui.QApplication(sys.argv)

        def qtSchedule(callback):
                timer=QtCore.QTimer(app)
                QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), lambda : callback(17))
                timer.start(17)
        schedule=qtSchedule

        def qtRun():
                app.exec_()
        run=qtRun

	setLightPosition = lambda lightPos : None
	drawVBO=lambda v: None
	load=lambda path, scale, group: None
	createVBO=lambda group: None
	deleteVBO=lambda vbo: None
	deleteMesh=lambda mesh: None
	getMeshPath=lambda mesh: ''
	getUvPath=lambda mesh, uvId: ''
	setupTex=lambda mesh, uvId, texId: None
	getMid=lambda centre_mesh, mid: None
	setupRotation=lambda x, y, z, wr, xr, yr, zr, xmid, ymid, zmid, xorig, yorig, zorig: None
	drawToTex=lambda mesh, alpha, fbo, width, height, bg, boundPlane, top
	draw=lambda mesh, alpha: None
	drawRotated=lambda xPos, yPos, zPos, wAtt, xAtt, yAtt, zAtt, wAng, xAng, yAng, zAng, p_centre_mesh, alpha, p_mesh: None
	imageLoad=lambda path: None
	glPushMatrix=lambda : None
	glPopMatrix=lambda : None
	glLoadIdentity=lambda : None
	glDisable=lambda flag: None
	glBegin=lambda prim: None
