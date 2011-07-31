import pyglet
pyglet.options['audio'] = ('directsound', 'openal', 'alsa', 'silent')

from euclid import *

from pyglet.media import *
from traceback import print_exc

from manage import sound_effects

class SoundSlot(object):
    def __init__(self, name="", loop=False, pos=None, snd=None):
        self.__name=name
        self.__loop=loop
        self.__player=None
        self.__pos=pos
        self.__snd=snd
 
    def stop(self):
        self.__player.stop()

    @property
    def pitch(self):
        return self.__player.pitch

    @pitch.setter
    def pitch(self, value):
         self.__player.pitch=value

    def play(self, snd=None, pos=None):
        if snd:
            self.__snd=snd
        if pos:
            self.__pos=pos
        if self.__player:
            self.__player.pause()
            was_playing=True
        self.__player=Player()
        try:
            assert self.__snd
            if self.__pos:
                self.__player.position=(self.__pos.x, self.__pos.y, self.__pos.z)
                #self.__player.position=(0, 0, 0)
            if self.__loop:
                self.__player.eos_action=Player.EOS_LOOP
            if not sound_effects:
                return
            self.__player.min_distance=10
            self.__player.queue(self.__snd)
            self.__player.play()
        except:
            print_exc()

    def setPos(self, pos):
        self.__pos=pos
        #print 'plane: '+str(self.__pos)

GUN_SND=load('data/spitfire_gun.wav', streaming=False)
ENGINE_SND=load('data/spitfire_engine.wav', streaming=False)

def setListener(eye, pos, zen):
    listener.position=(eye.x-pos.x, eye.y-pos.y, eye.z-pos.z)
    f=pos
    if f.z==0:
        f.z=0.0000001
    listener.forward_orientation=(f.x, f.y, f.z)
    z=zen.copy()
    listener.up_orientation=(zen.x, zen.y, zen.z)
