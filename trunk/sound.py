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
            #if self.__pos:
            #    self.__player.position=(self.__pos.x, self.__pos.y, self.__pos.z)
                #self.__player.position=(0, 0, 0)
            if self.__loop:
                self.__player.eos_action=Player.EOS_LOOP
            if not sound_effects:
                return
            self.__player.queue(self.__snd)
            self.__player.play()
        except:
            print_exc()

    def setPos(self, pos):
        self.__pos=pos
        self.__pos=Vector3(0,0,0)

GUN_SND=load('data/spitfire_gun.wav', streaming=False)
ENGINE_SND=load('data/spitfire_engine.wav', streaming=False)

def setListener(eye, pos, zen):
    listener.position=eye
    listener.forward_orientation=pos
    listener.up_orientation=zen
    
    #where listener is
    #listener.position=(pos.x-10, pos.y-10, pos.z-10)
    #impact
    #listener.forward_orientation=(-20,0,0)
    #listener.up_orientation=(0,0,0)

    #print 'center: '+str(pyglet.media.listener.position)+' eye: '+str(listener.forward_orientation)+' up: '+str(listener.up_orientation)
