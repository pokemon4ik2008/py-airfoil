import os

retVal = 0
cmd = ''


if os.name == 'nt':
	cmd = '"\"%VS80COMNTOOLS%..\IDE\devenv.exe\"" c\object3d.vcproj /build debug /Out buildlog2.txt'
elif os.name == 'posix':
	cmd = 'g++ c/objects.cpp c/collider.cpp -Ic -Ic/Eigen -lGLEW -lGLU -lGL -o bin/object3d.so -O3 -shared -fPIC'

print "Running build command : \n" + cmd
retVal = os.system(cmd)
if retVal == 0:
	print "Build success : objects"
else:
	print "Build failed : objects"


if os.name == 'nt':
        cmd = '"\"%VS80COMNTOOLS%..\IDE\devenv.exe\"" c\cterrain.vcproj /build debug /Out buildlog.txt'
elif os.name == 'posix':
	cmd = 'g++ c/cterrain.c c/collider.cpp -Ic -Ic/Eigen -I/usr/X11R6/include -I/usr/local/include -lMini -lGL -lGLU -o bin/cterrain.so -O3 -shared -fPIC'

print "Running build command : \n" + cmd
retVal = os.system(cmd)
if retVal == 0:
        print "Build success : cterrain"
else:  
        print "Build failed : cterrain"

