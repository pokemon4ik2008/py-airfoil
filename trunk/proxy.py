import cPickle

from collections import deque
import ctypes
import errno
from euclid import Quaternion, Vector3
import manage
from Queue import LifoQueue
import re
import select
import socket
from subprocess import Popen, PIPE
import sys
from threading import Condition, RLock, Thread
from time import sleep, time
from traceback import print_exc
from util import getLocalIP, int2Bytes, bytes2Int, toHexStr

from async import Scheduler

PORT=8124
LEN_LEN=4

def droppable(flags):
    return (flags & Mirrorable.DROPPABLE_FLAG)==Mirrorable.DROPPABLE_FLAG

class Mirrorable:
    META=0
    __INDEXES=[TYP_IDX, IDENT, SYS, FLAGS]=range(4)
    _SIZES = [2, 2, 2, 1]
    UPDATE_SIZE=META_SIZE=sum(_SIZES)
    SHIFTS = [sum(_SIZES[:i]) for i in __INDEXES]
    InstCount = 0
    _DEAD_FLAG=0x1
    DROPPABLE_FLAG=0x2

    def __init__(self, typ, ident=None, proxy=None, uniq=None):
        self._client_id=0
        self._proxy=proxy
        try:
            assert typ<=SerialisableFact.getMaxType()
        except AssertionError:
            print >> sys.stderr, 'Mirrorable.__init__. typ too large: '+str(typ)
        self.__typ=typ
        self._flags=0
	self.collidable=False
        if ident is None:
            self.__local=True
            self.localInit()
        else:
            self.__local=False
            self.remoteInit(ident)

    def __repr__(self):
        if self._client_id != 0:
            return str(self.getId())
        else:
            return str((None, self._ident))

    def mine(self):
        return self.__local or self._client_id==Client.PROXY.getSysId()

    def myBot(self):
        return not self.__local and self._client_id==Client.PROXY.getSysId()

    def local(self):
        return self.__local

    def localInit(self):
        (self._client_id, self._ident)=(Client.PROXY.getSysId(), Mirrorable.InstCount)
        Mirrorable.InstCount+=1

    def remoteInit(self, ident):
        (self._client_id, self._ident)=ident

    def isClose(self, obj):
        return False

    def estUpdate(self):
        pass

    def droppable(self):
        return droppable(self._flags)

    def __lt__(self, o):
        if o is None:
            return False
        (mySysId, myId)=self.getId()
        (oSysId, oId)=self.getId()
        if myId<oId:
            return True
        if mySysId<oSysId:
            return True
        return False

    def getId(self):
        #must return same type as deSerIdent
        #return (Sys.ID.getSysId(), self._ident)
        return (self._client_id, self._ident)

    def markChanged(self, full_ser=False):
        try:
            assert self.local()
            self._proxy.addUpdated(self, full_ser)
            return self.alive()
        except AssertionError:
            print_exc()
            return False

    def getType(self):
        return self.__typ

    def alive(self):
        return (self._flags & self._DEAD_FLAG)==0

    def markDead(self):
        try:
            assert self.local()
            self._flags &= ~self.DROPPABLE_FLAG
            self._flags |= self._DEAD_FLAG
        except AssertionError:
            print_exc()

    @property
    def flags(self):
        return self._flags

    @flags.setter
    def flags(self, value):
        self._flags=value

    def serialise(self):
        return [ ''.join([int2Bytes(field, size) for (field, size) in zip([self.__typ, self._ident, Client.PROXY.getSysId(), self._flags], self._SIZES)])]

    @staticmethod
    def deSerGivenMeta(meta, idx):
        start_shift=Mirrorable.SHIFTS[idx]
        return bytes2Int(meta[start_shift:start_shift+Mirrorable._SIZES[idx]])

    @staticmethod
    def deSerMeta(serialised, idx):
        start_shift=Mirrorable.SHIFTS[idx]
        return bytes2Int(serialised[Mirrorable.META][start_shift:start_shift+Mirrorable._SIZES[idx]])

    @staticmethod
    def deSerIdent(serialised):
        start_sys=Mirrorable.SHIFTS[Mirrorable.SYS]
        return (Mirrorable.deSerMeta(serialised, Mirrorable.SYS), Mirrorable.deSerMeta(serialised, Mirrorable.IDENT))

    def deserialise(self, serialised, estimated=False):
        flags=Mirrorable.deSerMeta(serialised, self.FLAGS)
        self._flags=flags
        return self

    def serNonDroppable(self):
        self._flags &= ~self.DROPPABLE_FLAG
        return []

    def deserNonDroppable(self, *args):
        return self

class ControlledSer(Mirrorable):
    UPDATE_SIZE=Mirrorable.META+11
    [ _POS,_,_, _ATT,_,_,_, _VEL,_,_ ] = range(Mirrorable.META+1, UPDATE_SIZE)

    def __init__(self, typ, ident=None, proxy=None):
        Mirrorable.__init__(self, typ, ident, proxy)

    def localInit(self):
        Mirrorable.localInit(self)
        self._flags |= self.DROPPABLE_FLAG

    def serialise(self):
        ser=Mirrorable.serialise(self)
        p=self.getPos()
        ser.append(p.x)
        ser.append(p.y)
        ser.append(p.z)
        a=self.getAttitude()
        ser.append(a.w)
        ser.append(a.x)
        ser.append(a.y)
        ser.append(a.z)
        v=self.getVelocity()
        ser.append(v.x)
        ser.append(v.y)
        ser.append(v.z)
        return ser

    @staticmethod
    def genAssign(ser, idx, size): 
        return [ dim for dim in ser[idx: idx+size] ]       

    @staticmethod
    def vAssign(ser, idx):
        return ControlledSer.genAssign(ser, idx, 3)

    @staticmethod
    def qAssign(ser, idx):
        return ControlledSer.genAssign(ser, idx, 4)

    def deserialise(self, ser, estimated=False):
        (px, py, pz)=ControlledSer.vAssign(ser, ControlledSer._POS)
        (aw, ax, ay, az)=ControlledSer.qAssign(ser, ControlledSer._ATT)
        (vx, vy, vz)=ControlledSer.vAssign(ser, ControlledSer._VEL)
        
        return Mirrorable.deserialise(self, ser, estimated).setPos(Vector3(px,py,pz)).setAttitude(Quaternion(aw,ax,ay,az)).setVelocity(Vector3(vx,vy,vz))

    def isClose(self, obj):
        if (self.getPos()-obj.getPos()).magnitude_squared()>=0.22:
            return False
        perm_att=self.getAttitude()
        temp_att=obj.getAttitude().conjugated()
        diff=(perm_att*temp_att)
        
        #print 'isClose: '+str(Vector3(diff.x, diff.y, diff.z).magnitude_squared())
        return Vector3(diff.x, diff.y, diff.z).magnitude_squared()<0.0001

class SerialisableFact:
    __OBJ_IDX,__TIME_IDX=range(2)
    HIT_CNT=0
    TOT_CNT=0

    def __init__(self, ctors):
        self.__notMine={}
        self.__objByType=[ [] for i in range(SerialisableFact.getMaxType()+1)]
        self.__mine={}
        self.__myObjsByType=[ [] for i in range(SerialisableFact.getMaxType()+1)]
        try:
            assert len(self.__objByType)==SerialisableFact.getMaxType()+1
        except:
            print 'SerialisableFact.__init__. objByTypeField wrong size: '+str(self.__objByType)
        self.__ctors=ctors

    def update(self, new_ctors):
        self.__ctors.update(new_ctors)

    @staticmethod
    def getMaxType():
        return 3

    @staticmethod
    def loads(obj_str):
        meta=obj_str[:Mirrorable.META_SIZE]
        obj=[meta]
        obj.extend(cPickle.loads(obj_str[Mirrorable.META_SIZE:]))
        return obj

    def estimable(self, mirrorable):
        try:
            # we compare mirrorable which is local with it deserialised version
            assert mirrorable.local()
            self.__class__.TOT_CNT+=1
            if mirrorable.getId() not in self.__mine:
                #print 'estimable. False 1'
                return False
            if mirrorable.isClose(self.__mine[mirrorable.getId()]):
                self.__class__.HIT_CNT+=1
                #print 'estimable. True'
                return True
            else:
                #print 'estimable. False 2'
                return False
        except AssertionError:
            print_exc()

    def deserManyTo(self, identifier, serialised, objLookup, objByType, estimated=False):
        try:
            if identifier in objLookup:
                obj=objLookup[identifier]
                typ=obj.getType()
            else:
                typ=Mirrorable.deSerMeta(serialised, Mirrorable.TYP_IDX)
                if typ in self.__ctors:
                    obj = self.__ctors[typ](ident=identifier)
                    objLookup[identifier] = obj
                    objByType[typ].append(obj)
                else:
                    assert False
            obj.deserialise(serialised, estimated)
            if len(serialised)>obj.UPDATE_SIZE:
                obj.deserNonDroppable(*serialised[obj.UPDATE_SIZE:])
            if not obj.alive():
                del(objLookup[identifier])
                objByType[obj.getType()].remove(obj)
        except AssertionError:
            print >> sys.stderr, 'deserialiseAll. unrecognised typ: '+str(typ)+' '+str(serialised)
            print_exc()

    def deserRemotes(self, sers):
        for identifier in sers:
            serialised=SerialisableFact.loads(sers[identifier])
            self.deserManyTo(identifier, serialised, self.__notMine, self.__objByType)

    def deserLocal(self, identifier, serialised, estimated=False):
        self.deserManyTo(identifier, serialised, self.__mine, self.__myObjsByType, estimated)
        
    def __contains__(self, ident):
        return ident in self.__mine or ident in self.__notMine

    def getObj(self, ident):
        try:
            if ident in self.__mine:
                return self.__mine[ident]
            return self.__notMine[ident]
        except KeyError:
            print_exc()
            print 'Client.getObj. id: '+str(ident)+' mine: '+str(self.__mine.keys())+' not mine: '+str(self.__notMine.keys())

    def getTypeObjs(self, typ, native=True, foreign=True):
        objs=[]
        try:
            assert typ<=SerialisableFact.getMaxType()
            if native:
                objs.extend(self.__myObjsByType[typ])
            if foreign:
                objs.extend(self.__objByType[typ])
        except AssertionError:
            print 'getTypeObjs. typ too large: '+str(typ)
        return objs

    def getTypesObjs(self, types, native=True, foreign=True):
        objs=[]
        for t in types:
            objs.extend(self.getTypeObjs(t, native, foreign))
        return objs

def read(s, rec, addSend, finalise):
    start=0
    cur_len_in=0
    cur_len_in_s=''
    len_left=LEN_LEN
    read_len=0
    #print 'read. len: '+str(len(rec))+' start: '+str(start)+' rec: '+toHexStr(rec)
    read_len=len(rec[start:])
    while read_len >= LEN_LEN+cur_len_in:
        cur_len_in = bytes2Int(rec[start:start+LEN_LEN])
        #print 'read. read_len: '+str(read_len)+' cur_len_in: '+str(cur_len_in)
        if read_len>=LEN_LEN+cur_len_in:
            #print 'read. addSend: len: '+toHexStr(rec[start:start+LEN_LEN])+' obj: '+toHexStr(rec[start+LEN_LEN:start+LEN_LEN+cur_len_in])
            addSend(s, rec[start:start+LEN_LEN], rec[start+LEN_LEN:start+LEN_LEN+cur_len_in])
            start+=LEN_LEN+cur_len_in
            read_len=len(rec[start:])
            cur_len_in=0
    finalise(s)
    return rec[start:]

class Client(Thread, Mirrorable):
     PROXY=None
     TYP=1
     __TOP_UP_LEN=32

     def initSys(self, ident):
         print 'initSys. after deserialising '+str(self._client_id)+' new: '+str(ident)
         #Sys.ID=Sys(ident)
         #self.__readSysId()
         if self._client_id==0:
             (self._client_id, filler)=ident
             Client.PROXY=self
             self.markChanged()
         print 'initSys: id '+str(Client.PROXY)
         return self

     def __init__(self, ident=None, server=getLocalIP(), port=PORT, factory=None):
         print 'Client.__init__. ident: '+str(ident)
         self.__server=server
         self.__port=port
         self.__fact=factory
         Mirrorable.__init__(self, self.TYP, ident, self)

     #def __readSysId(self):
     #    self._client_id=Sys.ID.getSysId()

     #overriding as default implementation requires that Client.PROXY is already set
     def serialise(self):
         return [ ''.join([int2Bytes(field, size) for (field, size) in zip([self.TYP, self._ident, self._client_id, self._flags], self._SIZES)])]

     def getSysId(self):
         return self._client_id

     def localInit(self):
         Thread.__init__(self)
         #Mirrorable.localInit(self)
         self._ident=Mirrorable.InstCount
         Mirrorable.InstCount+=1
         self.__fact.update({ Client.TYP: self.initSys })
         self.__dead_here=False
         self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         self.__s.setblocking(0)
         try:
             print 'Client. connecting'
             self.__s.connect((self.__server, self.__port))
         except socket.error as (errNo, errStr):
             if errNo==115:
                 #EINPROGRESS
                 pass
             else:
                 print >> sys.stderr, "Client.__init__ failed to connect: "+str(errNo)+" "+errStr
         self.__serialised=dict()
         self.__sers={}
         self.__ids=deque()
         self.__locked_serialised=dict()
         self.__outbox=deque()
         self.__out=''
         self.__in=''
         self.bytes_read=0
         self.bytes_sent=0
         self.__lock=RLock()
         self.__open=True
         self.daemon=True
         self.start()

     def attemptSendAll(self):
         if self.acquireLock() and Client.PROXY is not None:
             if not self.alive():
                 print 'sending tail: '+str(len(self.__ids))
             while len(self.__ids)>0:
                 unique=self.__ids.popleft()
                 if unique not in self.__locked_serialised:
                     self.__outbox.append(unique)
                 self.__locked_serialised[unique]=self.__serialised[unique][:]

             if len(self.__outbox)>0:
                 start_time=time()
                 self.send()
                 end_send=time()
                 if end_send-start_time>=0.1:
                     print 'hmmm...send just blocked. this is unexpected: '+(str(end_send-start_time))
             else:
                 if not self.alive():
                     print 'client is dead'
                     self.quit()

             self.__serialised=dict()
             done=len(self.__outbox)==0
             self.releaseLock()
             return done
         return False

     def __pushSend(self, uniq, ser):
         if uniq not in self.__serialised:
             self.__ids.append(uniq)
         self.__serialised[uniq]=ser

     def addUpdated(self, mirrorable, full_ser):
         try:
             #can't get any obj id if we don't have a sys id
             assert Client.PROXY is not None
             assert mirrorable.local()

             uniq=mirrorable.getId()
             ser=mirrorable.serialise()
             if full_ser:
                 ser+=mirrorable.serNonDroppable()
             if uniq in self.__fact and manage.fast_path:
                 self.__fact.getObj(uniq).estUpdate()
             if not mirrorable.droppable() or not self.__fact.estimable(mirrorable):
                 self.__pushSend(uniq, ser)
                 if manage.fast_path:
                     self.__fact.deserLocal(uniq, ser)
                 #print 'flags: '+str(mirrorable.flags)
                 #if not mirrorable.droppable():
                 #    mirrorable.flags|=Mirrorable.DROPPABLE_FLAG
             else:
                 self.__fact.deserLocal(uniq, ser, estimated=True)
             self.attemptSendAll()
         except AssertionError:
             print_exc()

     def acquireLock(self, blocking=False):
         return self.__lock.acquire(blocking)

     def releaseLock(self):
         self.__lock.release()

     def __contains__(self, ident):
         return ident in self.__fact

     def getObj(self, ident):
         return self.__fact.getObj(ident)

     def getTypeObjs(self, typ, native=True, foreign=True):
         return self.__fact.getTypeObjs(typ)

     def getTypesObjs(self, types):
         return self.__fact.getTypesObjs(types)

     def send(self):
         if not self.alive():
             print 'sending: '+str(len(self.__outbox))
         unique=self.__outbox.popleft()
         obj=self.__locked_serialised[unique]
         del(self.__locked_serialised[unique])
         obj_s=obj[Mirrorable.META]+cPickle.dumps(obj[Mirrorable.META+1:])
         obj_len=int2Bytes(len(obj_s), LEN_LEN)
         #print 'send: len: '+str(len(obj_s))+' encoded: '+toHexStr(obj_len)
         #obj_len='%10s' %len(obj_s)
         self.__out+=obj_len
         self.__out+=obj_s
         sent=0
         try:
             assert len(self.__out)>0
             sent=self.__s.send(self.__out)
             while sent!=0:
                 self.bytes_sent+=sent
                 self.__out=self.__out[sent:]
                 sent=self.__s.send(self.__out)
         except AssertionError:
             print >> sys.stderr, 'tried to send 0 bytes outbox: '+str(len(self.__outbox))
         except IOError, e:
             if e.errno != errno.EAGAIN:
                 print_exc()

     def addSerialisables(self, s, obj_len, obj_str):
         #print 'addSerialisables. obj_len: '+str(obj_len)+' '+toHexStr(obj_str[:Mirrorable.META_SIZE])
         meta=obj_str[:Mirrorable.META_SIZE]
         uniq=(Mirrorable.deSerGivenMeta(meta, Mirrorable.SYS), Mirrorable.deSerGivenMeta(meta, Mirrorable.IDENT)) 
         self.__sers[uniq]=obj_str

     def quit(self):
         try:
             print 'Client.quit. shutdown sock'
             self.__s.shutdown(socket.SHUT_RDWR)
             self.__s.close()
         except:
             print_exc()
         self.__open=False
         print 'Client is quitting'

     def run(self):
         cur_len_in_s=''
         cur_len_in=0
         len_left=LEN_LEN
         start=0
         read_len=0
         rec=''
         worker=Scheduler(block=True, receive=False)
         
         try:
             while(self.__open):
                 sleep_needed=False
                 if self.alive():
                     #sends done from main loop
                     writers=[]
                 #else:
                     #not longer in main loop
                     #writers=[self.__s]
                     #print 'proxy is dead. add writer to select'
                 reads, writes, errs = select.select([self.__s], writers, [], 1.5)
                 if self.acquireLock(True):
                     try:
                         if self.__s in reads:
                             #if self.acquireLock(True):
                                 read_now=self.__s.recv(4096)
                                 self.bytes_read+=len(read_now)
                                 if read_now=='':
                                     self.markDead()
                                     self.releaseLock()
                                     self.__open=False
                                     break
                                 #print 'Client.run: len read: '+str(len(rec))
                                 rec=read(self.__s, rec+read_now, self.addSerialisables, lambda sock: None)
                                 self.__fact.deserRemotes(self.__sers)
                                 self.__sers={}
                                 if self.getId() in self.__fact and not self.getObj(self.getId()).alive():
                                     print 'Client.run. closing socket'
                                     self.releaseLock()
                                     self.__open=False
                                     break
                                 #self.releaseLock()
                             #else:
                             #    sleep_needed=True
                         if self.__s in writes:
                             if not self.alive():
                                 print 'after select. proxy is dead and socket is writeable'
                             #if self.acquireLock():
                             if not self.alive():
                                 print 'after select. proxy is dead and socket is writeable and we have the lock'
                             if len(self.__outbox)>0:
                                 if not self.alive():
                                     print 'after select. proxy is dead and socket is writeable and we have the lock and we have something to send'
                                 self.send()
                             else:
                                 sleep_needed=True
                             #self.releaseLock()
                             #else:
                             #    sleep_needed=True
                     finally:
                         self.releaseLock()
                 if sleep_needed:
                     sleep(0)
         except:
             if self.alive():
                 print 'exception in client'
                 self.markDead()
                 print_exc()
                 self.quit()
         print 'Exiting Client.run'

class Sys(Mirrorable):
    TYP=2
    
    def __init__(self, ident=None, proxy=None):
        print 'Sys: ident: '+str(ident)+' '+str(proxy)
        self.__sysId=0
        if proxy is not None:
            while proxy.alive():
                if proxy.acquireLock():
                    if Client.PROXY is not None:
                        proxy.releaseLock()
                        break
                    proxy.releaseLock()
                sleep(1)
            (self.__sysId, client_inst)=proxy.getId()
        Mirrorable.__init__(self, Sys.TYP, ident)

    def getSysId(self):
        return self.__sysId

    def markChanged(self):
        raise NotImplementedError

    #def serialise(self):
    #    return [ ''.join([int2Bytes(field, size) for (field, size) in zip([self.TYP, self._ident, 0, self._flags], self._SIZES)])]

class Server(Thread):
    def __init__(self, server=getLocalIP(), port=PORT, own_thread=True):
         Thread.__init__(self)
         self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         self.__s.setblocking(0)
         #self.__s.bind((gethostname(), port))
         self.__s.bind((server, port))
         self.__s.listen(5)
         self.__readers, self.__writers = ([], [])
         self.__in={}
         self.__serialisables={}
         self.__stopped=False
         self.__outQs={}
         self.__outs={}
         self.__nextInst=1
         self.bytes_read=0
         self.bytes_sent=0
         self.daemon=True
         self.__accepted_clients=False
         if own_thread:
             self.start()
         else:
             self.run()

    def recWrites(self, s, obj_len, obj_str):
        fields=[ Mirrorable.deSerGivenMeta(obj_str, field) for field in [Mirrorable.SYS, Mirrorable.IDENT, Mirrorable.FLAGS]]
        uniq=(fields[0], fields[1])
        flags=fields[2]

        if uniq not in self.__outs[s]:
            #print 'recWrites: '+str(uniq)+' dict: '+str(self.__outs[s])
            self.__outQs[s].append(uniq)
        self.__outs[s][uniq]=obj_str;

        if not droppable(flags):
            self.qWrites(s)

    def qWrite(self, s, string):
        #print 'qWrite. s: '+str(s)+' string: '+toHexStr(string)
        self.__serialisables[s]+=string
        if s not in self.__writers:
            self.__writers.append(s)

    def qWrites(self, s):
        try:
            for uniq in self.__outQs[s]:
                #print 'qWrites: '+str(uniq)
                obj_str=self.__outs[s][uniq]
                obj=int2Bytes(len(obj_str), LEN_LEN)+obj_str
                #print 'qWrites. readers: '+str(self.__readers)
                for reader in self.__readers:
                    if reader is not s or not manage.fast_path:
                        self.qWrite(reader, obj)
        except KeyError:
            print >> sys.stderr, "qWrites. failed to find uniq: "+str(uniq)+' or sock: '+str(s)+' in dict: '+str(self.__outs)
            if s not in self.__outs:
                self.__outs[s]={}
        self.__outQs[s]=[]
        self.__outs[s]={}

    def __remove_sock(self, s):
        del self.__serialisables[s]
        if s in self.__writers:
            self.__writers.remove(s)
        self.__readers.remove(s)

    def close(self, s):
        self.__remove_sock(s)
        try:
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        except:
            print_exc()

    def quit(self):
        print 'Server.quit'
        for s in set(self.__readers):
            try:
                self.close(s) 
            except:
                print_exc()
        try:
            self.__s.shutdown(socket.SHUT_RDWR)
            self.__s.close()
        except:
            print_exc()

    def running(self):
        if not manage.proxy:
            return True
        return not(self.__readers==[] and self.__accepted_clients)

    def run(self):
        try:
            while self.running():
                try:
                    reads, writes, errs = select.select(self.__readers+[self.__s], self.__writers, [], 60)
                    if manage.proxy is not None and not manage.proxy.alive():
                        print 'Server.run. client dead.'
                    for r in reads:
                        try:
                            if r is self.__s:
                                (sock, address) = r.accept()
                                print 'accepted from '+str(address)
                                assert sock not in self.__readers
                                self.__readers.append(sock)
                                assert sock not in self.__serialisables
                                assert sock not in self.__writers
                                self.__serialisables[sock]=''
                                client=Client((self.__nextInst,0)).serialise()
                                self.__nextInst+=1
                                print 'client: '+str(client)
                                client_s=client[Mirrorable.META]+cPickle.dumps(client[Mirrorable.META+1:])
                                #print 'client: serialised. '+toHexStr(client_s)
                                self.qWrite(sock, int2Bytes(len(client_s), LEN_LEN)+client_s)
                                #print 'server.run. len '+str(len(client_s))+' '+toHexStr(int2Bytes(len(client_s), LEN_LEN))
                                #self.qWrite(client, '%10s' %len(client_s)+client_s)
                                self.__in[sock]=''
                                self.__accepted_clients=True
                            else:
                                self.__outQs[r]=[]
                                self.__outs[r]={}
                                read_now=r.recv(4096)
                                self.bytes_read+=len(read_now)
                                if read_now=='':
                                    self.__remove_sock(r)
                                    print 'closing server connection'
                                else:
                                    self.__in[r]=read(r, self.__in[r]+read_now, self.recWrites, self.qWrites)
                        except AssertionError:
                            print >> sys.stderr, 'Server.run. failed assertion on read'
                            print_exc()
                            self.quit()
                            print 'Exiting Server.run 4'
                            return
                        except socket.error as (errNo, errStr):
                            if errNo==104:
                                #Connection reset by peer
                                self.__remove_sock(r)
                            else:
                                print >> sys.stderr, "Server.run: exception on read. "+str((errNo,errStr))
                                print_exc()
                                self.quit()
                                print 'Exiting Server.run 3'
                                return
                    for w in writes:
                        try:
                            if w not in self.__serialisables:
                                #can happen just after closing a connection
                                continue
                            assert len(self.__serialisables[w]) > 0
                            #print 'Server.run. w: '+str(w)
                            sent=w.send(self.__serialisables[w])
                            self.bytes_sent+=sent
                            #print 'Client.run. sent: '+toHexStr(self.__serialisables[w][:sent])
                            if not sent:
                                print 'clising server connection 1'
                                self.__remove_sock(w)
                            else:
                                self.__serialisables[w]=self.__serialisables[w][sent:]
                                if len(self.__serialisables[w])==0:
                                    self.__writers.remove(w)

                        except AssertionError:
                            print >> sys.stderr, "proxy.run failed assertion on write"
                            print_exc()
                            self.quit()
                            print 'Exiting Server.run 2'
                            return
                        except socket.error as (errNo, errStr): 
                            if errNo==104:
                                #Connection reset by peer
                                self.__remove_sock(w)
                            else:
                                print >> sys.stderr, "Server.run: exception on write. "+str((errNo,errStr))
                                print_exc()
                                self.quit()
                                print 'Exiting Server.run 1'
                                return
                except select.error as (errNo, strErr):
                    print >> sys.stderr, 'select failed. err: '+str(errNo)+' str: '+strErr
                    eSock = None
                    try:
                        for r in self.__readers:
                            eSock = r
                            select.select([eSock], [],  [], 0)
                    except select.error:
                        self.__readers.remove(eSock)
                    try:
                        for w in self.__writers:
                            eSock=w
                            select.select([], [w],  [], 0)
                    except self.error:
                        self.__serialisables[eSock]=''
                        self.__writers.remove(eSock)
        except KeyboardInterrupt:
            pass
        except:
            print_exc()
        self.quit()
        print 'Exiting Server.run'
