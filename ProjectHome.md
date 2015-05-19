## About ##

This is an attempt at creating a simple simulator for modelling the behaviour of an aircraft in 3d space. The aim is not for ultimate realism but to create something that 'feels' like a aircraft.

![http://hourglassapps.com/py-airfoil/ext_screen_1.png](http://hourglassapps.com/py-airfoil/ext_screen_1.png)

It makes use of the following 3rd party libraries:
  * [pyglet](http://www.pyglet.org/) : provides access to OpenGL and allows reading the keyboard
  * [pyeuclid](http://code.google.com/p/pyeuclid/) : provides 3D math classes
  * [Duncan Casey's FractalTerrainMesh Generator](http://markmail.org/message/wxzfa75hrxafprjk) : terrain generator so that I can focus on the simulator rather than the graphics for the moment
  * [Eigen](http://eigen.tuxfamily.org/) : the C++ math library

## Installation ##
On Ubuntu Linux you need the following packages installed:
  * g++
  * mesa-common-dev
  * libglu1-mesa-dev
  * libglew1.5-dev
These can be installed using the command 'sudo apt-get install package'.

  1. You must first install pyglet. Download the [pyglet source distribution](http://pyglet.googlecode.com/files/pyglet-1.1.4.tar.gz). Run 'sudo python setup.py install'.
  1. Download the [source](https://code.google.com/p/py-airfoil/source/checkout)
  1. Change directory to the py-airfoil directory.
  1. Since the project includes c code it must first be compiled. This can be done by entering: `python scons.py`
  1. Run it as follows: `python simulate.py`