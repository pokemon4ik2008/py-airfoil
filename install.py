import os

retVal = 0
cmd = ''

if os.name == 'nt':
	cmd = '"\"%VS80COMNTOOLS%..\IDE\devenv.exe\"" c\cterrain\cterrain.vcproj /build debug /Out buildlog.txt'
elif os.name == 'posix':
	cmd = 'g++ c/cterrain/cterrain.c -lGL -o bin/cterrain.so -O3 -shared -fPIC'

print "Running build command : \n" + cmd
retVal = os.system(cmd)
if retVal == 0:
	print "Build success : airfoil"
else:
	print "Build failed : airfoil"

if os.name == 'nt':
	cmd = '"\"%VS80COMNTOOLS%..\IDE\devenv.exe\"" c\object3d\object3d.vcproj /build debug /Out buildlog2.txt'
elif os.name == 'posix':
	cmd = 'g++ c/object3d/objects.cpp -lGLEW -lGLU -lGL -o bin/object3d.so -O3 -shared -fPIC'

print "Running build command : \n" + cmd
retVal = os.system(cmd)
if retVal == 0:
	print "Build success : airfoil"
else:
	print "Build failed : airfoil"
