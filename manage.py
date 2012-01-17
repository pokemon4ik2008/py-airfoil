global proxy
proxy=None
global server
server=None
global fast_path
fast_path=True
global sound_effects
sound_effects=False
global opt
global vbo
vbo=True
from time import time
global now, delta

def updateTime():
    global now, delta
    n=time()
    delta=n-now
    now=n
    
now=time()
delta=0.0
