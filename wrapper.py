try:
        import pyglet
        from pyglet.gl import *
        from pyglet import window, font, clock # for pyglet 1.0
        from pyglet.window import key
        api='pyglet'
except ImportError:
        from PySide import QtCore, QtGui
        api='pyside'

if api=='pyglet':
        print 'pyglet installed'
        schedule=pyglet.clock.schedule
        run=pyglet.app.run
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
