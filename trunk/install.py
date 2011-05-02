import os

retVal = 0
cmd = ''

if os.name == 'nt':
	cmd = '"\"%VS80COMNTOOLS%..\IDE\devenv.exe\"" c\cterrain\cterrain.vcproj /build debug /Out buildlog.txt'
elif os.name == 'posix':
	cmd = 'g++ c/cterrain/cterrain.c -lGL -o bin/cterrain.so -shared -fPIC'

print "Running build command : \n" + cmd
retVal = os.system(cmd)
if retVal == 0:
	print "Build success"
else:
	print "Build failed"
