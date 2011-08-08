import pyglet
pyglet.options['audio'] = ('directsound', 'openal', 'alsa', 'silent')

from collections import deque
from euclid import *
from pyglet.media import *
import threading
from traceback import print_exc
import manage

class SoundSlot(object):
    __TID=None
    __PLAYING=set()
    __FREE=deque([ Player() for i in range(5) ])

    @staticmethod
    def checkTid():
        if SoundSlot.__TID is None:
            SoundSlot.__TID=threading.currentThread().ident
            return True
        else:
            return threading.currentThread().ident==SoundSlot.__TID

    @classmethod
    def sound_toggle(cls):
        try:
            assert cls.checkTid()
        except:
            print_exc()
        manage.sound_effects=not manage.sound_effects
        def free_player(player):
            player.pause()
            SoundSlot.__FREE.append(player)
        if not manage.sound_effects:
            [ free_player(p) for p in cls.__PLAYING ]
            cls.__PLAYING.clear()

    def __init__(self, name="", loop=False, pos=None, snd=None):
        try:
            assert self.checkTid()
        except:
            print_exc()
        self.__name=name
        self.__loop=loop
        self.__player=None
        self.__pos=pos
        self.__snd=snd

    def run(self, dt, *args, **kwargs):
        clock.unschedule(self.run)
        try:
            assert self.checkTid()
        except:
            print_exc()
        f=args[0]
        other_args=args[1:]
        f(self, *other_args, **kwargs)

    def schedule(self, f, *a, **kw):
        clock.schedule(self.run, *(f,)+a, **kw)

    def pause(self):
        try:
            assert self.checkTid()
        except:
            print_exc()
        self.__player.pause()
 
    @property
    def playing(self):
        try:
            assert self.checkTid()
        except:
            print_exc()
        return self.__player.playing

    @property
    def pitch(self):
        try:
            assert self.checkTid()
        except:
            print_exc()
        return self.__player.pitch

    @pitch.setter
    def pitch(self, value):
        try:
            assert self.checkTid()
        except:
            print_exc()
        self.__player.pitch=value

    def play(self, snd=None, pos=None):
        try:
            assert self.checkTid()
        except:
            print_exc()
        if snd:
            self.__snd=snd
        if pos:
            self.__pos=pos
        if not manage.sound_effects:
            return
        if self.__player and self.__player in self.__PLAYING:
            self.__player.pause()
            SoundSlot.__FREE.append(self.__player)
            self.__PLAYING.remove(self.__player)

        try:
            assert self.__snd
            self.__player=self.__FREE.popleft()
            if self.__pos:
                self.__player.position=(self.__pos.x, self.__pos.y, self.__pos.z)
            if self.__loop:
                self.__player.eos_action=Player.EOS_LOOP
            else:
                self.__player.eos_action=Player.EOS_PAUSE
            self.__player.min_distance=80
            self.__player.next()
            self.__player.queue(self.__snd)
            self.__player.play()
            @self.__player.event
            def on_eos():
                try:
                    assert self.checkTid()
                except:
                    print_exc()
                if self.__player and self.__player in self.__PLAYING and self.__player.eos_action!=Player.EOS_LOOP:
                    self.__PLAYING.remove(self.__player)
                    self.__FREE.append(self.__player)
            self.__PLAYING.add(self.__player)
        except:
            print_exc()

    def setPos(self, pos):
        try:
            assert self.checkTid()
        except:
            print_exc()
        self.__pos=pos
        self.__player.position=self.__pos

GUN_SND=load('data/gun.wav', streaming=False)
ENGINE_SND=load('data/spitfire_engine.wav', streaming=False)

def setListener(eye, pos, zen):
    listener.position=(eye.x, eye.y, eye.z)
    listener.forward_orientation=(pos.x, pos.y, pos.z)
    listener.up_orientation=(zen.x, zen.y, zen.z)
