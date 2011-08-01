import pyglet
pyglet.options['audio'] = ('directsound', 'openal', 'alsa', 'silent')

from euclid import *
from pyglet.media import *
from traceback import print_exc

import manage

class SoundSlot(object):
    __PLAYING=set()

    @classmethod
    def sound_off(cls):
        manage.sound_effects=not manage.sound_effects
        [ snd.pause() for snd in cls.__PLAYING ]
        cls.__PLAYING.clear()

    def __init__(self, name="", loop=False, pos=None, snd=None):
        self.__name=name
        self.__loop=loop
        self.__player=None
        self.__pos=pos
        self.__snd=snd

    def pause(self):
        self.__player.pause()
 
    @property
    def playing(self):
        return self.__player.playing

    @property
    def pitch(self):
        return self.__player.pitch

    @pitch.setter
    def pitch(self, value):
         self.__player.pitch=value

    def play(self, snd=None, pos=None):
        print 'sound. play'
        if snd:
            self.__snd=snd
        if pos:
            self.__pos=pos
        if self.__player:
            self.__player.pause()
        self.__player=Player()
        @self.__player.event
        def on_eos():
            print 'play. name: '+self.__name+' '+str(self.__player)
            self.__PLAYING.remove(self)
        try:
            assert self.__snd
            if self.__pos:
                self.__player.position=(self.__pos.x, self.__pos.y, self.__pos.z)
                #self.__player.position=(0, 0, 0)
            if self.__loop:
                self.__player.eos_action=Player.EOS_LOOP
            if not manage.sound_effects:
                print 'sounds off'
                return
            self.__player.min_distance=10
            self.__player.queue(self.__snd)
            self.__player.play()
            self.__PLAYING.add(self)
        except:
            print_exc()

    def setPos(self, pos):
        self.__pos=pos
        self.__player.position=self.__pos

GUN_SND=load('data/spitfire_gun.wav', streaming=False)
ENGINE_SND=load('data/spitfire_engine.wav', streaming=False)

def setListener(eye, pos, zen):
    listener.position=(eye.x, eye.y, eye.z)
    #listener.position=(eye.x-pos.x, eye.y-pos.y, eye.z-pos.z)
    listener.forward_orientation=(pos.x, pos.y, pos.z)
    listener.up_orientation=(zen.x, zen.y, zen.z)
