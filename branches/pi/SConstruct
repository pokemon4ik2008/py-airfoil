def CheckPKGConfig(context, version):
     context.Message( 'Checking for pkg-config... ' )
     ret = context.TryAction('pkg-config --atleast-pkgconfig-version=%s' % version)[0]
     context.Result( ret )
     return ret

def CheckPKG(context, name):
     context.Message( 'Checking for %s... ' % name )
     ret = context.TryAction('pkg-config --exists \'%s\'' % name)[0]
     context.Result( ret )
     return ret

# Configuration:


objEnv = Environment()

conf = Configure(objEnv, custom_tests = { 'CheckPKGConfig' : CheckPKGConfig,
                                       'CheckPKG' : CheckPKG })

if not conf.CheckPKGConfig('0.15.0'):
     print 'pkg-config >= 0.26.0 not found.'
     Exit(1)


graphics=True
libChecks=[('glew', '1.6.0'), ('glu', '8.0.5'), ('gl', '8.0.5')]
for (lib, ver) in libChecks:
        comparison=lib+' >= '+ver
        if not conf.CheckPKG(comparison):
                print comparison+' not found. graphics disabled'
                graphics=False
		break

objEnv.Append(CPPPATH = ['c', 'c/Eigen'])
if graphics:
        objEnv.Append(CCFLAGS='-O3 -DOPEN_GL')
        objEnv.ParseConfig('pkg-config --cflags --libs glew')
        objEnv.ParseConfig('pkg-config --cflags --libs glu')
        objEnv.ParseConfig('pkg-config --cflags --libs gl')
else:
        objEnv.Append(CCFLAGS='-O3 -DNO_GRAPHICS')
        objEnv.ParseConfig('pkg-config --cflags --libs gl')
        
collider=objEnv.SharedObject(target = 'bin/collider', source = ["c/collider.cpp"])
object3d=objEnv.SharedLibrary(target = 'bin/object3d', source = ["c/objects.cpp", collider])

terrEnv = objEnv.Clone()
terrEnv.Append(CPPPATH = ['c', 'c/Eigen', '/usr/X11R6/include', '/usr/local/include'])

if graphics:
     terrEnv.Append(LIBS = ['Mini'])

cterrain=terrEnv.SharedLibrary(target = 'bin/cterrain', source = ["c/cterrain.cpp", collider])
