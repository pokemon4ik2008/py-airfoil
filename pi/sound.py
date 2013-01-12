import pyglet
#unable to reuse Players when alsa is the selected driver on Paul's samsung laptop
#so alsa is disabled for now
#pyglet.options['audio'] = ('directsound', 'openal', 'alsa', 'silent')
pyglet.options['audio'] = ('directsound', 'openal', 'silent')

from collections import deque
from euclid import *
from pyglet.media import *
import thread
from traceback import print_exc
import manage

class SoundSlot(object):
    __TID=None
    __PLAYING=set()
    __FREE=deque([ Player() for i in range(15) ])
    __SCHEDULED=deque()

    @staticmethod
    def checkTid():
        if SoundSlot.__TID is None:
            SoundSlot.__TID=thread.get_ident()
            return True
        else:
            if thread.get_ident()!=SoundSlot.__TID:
                print 'checkTid. current: '+str(thread.get_ident())+' '+str(SoundSlot.__TID)+' '+str(thread.get_ident())
                return False
            else:
                return True

    @classmethod
    def free_player(cls, player):
        player.pause()
        player.volume=1.0
        player.pitch=1.0
        cls.__FREE.append(player)
        cls.__PLAYING.remove(player)

    @classmethod
    def sound_toggle(cls):
        try:
            assert cls.checkTid()
        except:
            print_exc()
        manage.sound_effects=not manage.sound_effects
        if not manage.sound_effects:
            [ cls.free_player(p) for p in set(cls.__PLAYING) ]

    def __init__(self, name="", loop=False, pos=None, snd=None):
        try:
            assert self.checkTid()
        except:
            print_exc()
        self.__name=name
        self.__loop=loop
        self.__player=None
        self.__pos=pos
        self.snd=snd

    def __free_player(self):
        SoundSlot.free_player(self.__player)

    def pause(self):
        try:
            assert self.checkTid()
        except:
            print_exc()
        if self.__player:
            self.__player.pause()
 
    @property
    def playing(self):
        try:
            assert self.checkTid()
        except:
            print_exc()
        return self.__player is not None and self.__player.playing

    @property
    def pitch(self):
        try:
            assert self.checkTid()
        except:
            print_exc()
        if self.__player:
            return self.__player.pitch
        return 0

    @pitch.setter
    def pitch(self, value):
        try:
            assert self.checkTid()
        except:
            print_exc()
        if self.__player:
            self.__player.pitch=value

    @property
    def volume(self):
        try:
            assert self.checkTid()
        except:
            print_exc()
        if self.__player:
            return self.__player.volume
        return 0

    @volume.setter
    def volume(self, value):
        try:
            assert self.checkTid()
        except:
            print_exc()
        if self.__player:
            self.__player.volume=value

    def play(self, snd=None, pos=None):
        try:
            assert self.checkTid()
        except:
            print_exc()
        if snd:
            self.snd=snd
        if pos:
            self.__pos=pos
        if not manage.sound_effects:
            return
        if self.__player and self.__player in self.__PLAYING:
            self.__free_player()
        try:
            assert self.snd
            self.__player=self.__FREE.popleft()
            if self.__pos:
                self.__player.position=(self.__pos.x, self.__pos.y, self.__pos.z)
            if self.__loop:
                self.__player.eos_action=Player.EOS_LOOP
            else:
                self.__player.eos_action=Player.EOS_PAUSE
            self.__player.min_distance=80
            self.__player.next()
            self.__player.queue(self.snd)
            self.__player.play()
            @self.__player.event
            def on_eos():
                try:
                    assert self.checkTid()
                except:
                    print_exc()
                if self.__player and self.__player in self.__PLAYING and self.__player.eos_action!=Player.EOS_LOOP:
                    self.__free_player()
            self.__PLAYING.add(self.__player)
        except:
            print_exc()

    def setPos(self, pos):
        try:
            assert self.checkTid()
        except:
            print_exc()
        self.__pos=pos
        if self.__player:
            self.__player.position=self.__pos

GUN_SND=load('data/gun.wav', streaming=False)
ENGINE_SND=load('data/spitfire_engine.wav', streaming=False)
SCREECH_SND=load('data/104026__rutgermuller__Tire_Squeek_www.rutgermuller.wav', streaming=False)
WIND_SND=load('data/34338__ERH__wind.wav', streaming=False)
WHIZZ_SND=load('data/90782__kmoon__bullet-flyby-2.wav', streaming=False)
IMPACT_SND=load('data/116645__woodingp__bullets-hit-edit.wav', streaming=False)
GRIND_SND=load('data/10338__batchku__no-escape.wav', streaming=False)

def setListener(eye, pos, zen):
    listener.position=(eye.x, eye.y, eye.z)
    listener.forward_orientation=(pos.x, pos.y, pos.z)
    listener.up_orientation=(zen.x, zen.y, zen.z)
