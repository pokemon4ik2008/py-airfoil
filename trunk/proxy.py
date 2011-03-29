from airfoil import Airfoil
import cPickle
from collections import deque
from euclid import Quaternion, Vector3
from Queue import LifoQueue
import re
import select
import socket
from subprocess import Popen, PIPE
import sys
from threading import Condition, RLock, Thread
from time import sleep
from traceback import print_exc

PORT=8123

class Mirrorable:
    META=0
    __INDEXES=[TYPE, IDENT, SYS, FLAGS]=range(4)
    _SIZES = [2, 2, 2, 1]
    META_SIZE=sum(_SIZES)
    SHIFTS = [sum(_SIZES[:i]) for i in __INDEXES]
    __InstCount = 0
    __DEAD_FLAG=1

    def __init__(self, typ, ident=None, proxy=None, uniq=None):
        self._proxy=proxy
        try:
            assert typ<=SerialisableFact.getMaxType()
        except AssertionError:
            print >> sys.stderr, 'Mirrorable.__init__. typ too large: '+str(typ)
        self.__typ=typ
        self._dead=False
        if ident is None:
            self.local_init()
        else:
            self.remote_init(ident)

    def local_init(self):
        self._ident=Mirrorable.__InstCount
        Mirrorable.__InstCount+=1

    def remote_init(self, ident):
        (client_id, my_ident)=ident
        self._ident=my_ident

    def getId(self):
        try:
            assert Sys.ID is not None
            #must return same type as deSerIdent
            return (Sys.ID.getSysId(), self._ident)
        except AssertionError:
            print >> sys.stderr, 'Mirrorable.getId. System setup incomplete. '+str((self.__typ, self._ident))
        return (0, self._ident)

    def markChanged(self):
        if self._proxy is None:
            raise NotImplementedError
        self._proxy.addUpdated(self)
        return self.alive()

    #def getUnique(self):
    #    return (self.__typ, self.getId())    

    def alive(self):
        return not self._dead

    def markDead(self, dead=True):
        self._dead=dead

    @staticmethod
    def int2Bytes(i, size):
        s=''
        for idx in range(size):
            s+=chr((i >> (idx*8)) & 0xff)
        return s

    @staticmethod
    def bytes2Int(s):
        i=0
        for idx in range(len(s)):
           i |= ord(s[idx]) << (idx*8) 
        return i

    def serialise(self):
        return [ ''.join([Mirrorable.int2Bytes(field, size) for (field, size) in zip([self.__typ, self._ident, Sys.ID.getSysId(), self._dead], self._SIZES)])]
        #return [self.__typ, self._ident, self.__dead]

    @staticmethod
    def deSerMeta(serialised, idx):
        start_shift=Mirrorable.SHIFTS[idx]
        return Mirrorable.bytes2Int(serialised[Mirrorable.META][start_shift:start_shift+Mirrorable._SIZES[idx]])

    @staticmethod
    def deSerIdent(serialised):
        start_sys=Mirrorable.SHIFTS[Mirrorable.SYS]
        return (Mirrorable.deSerMeta(serialised, Mirrorable.SYS), Mirrorable.deSerMeta(serialised, Mirrorable.IDENT))

    def deserialise(self, serialised):
        self.markDead(Mirrorable.deSerMeta(serialised, self.FLAGS) & self.__DEAD_FLAG == self.__DEAD_FLAG)
        return self

class ControlledSer(Mirrorable):
    TYP=0
    [ _POS,_,_, _ATT,_,_,_, _VEL,_,_, _THRUST ] = range(Mirrorable.META+1, Mirrorable.META+12)

    def __init__(self, ident=None, proxy=None):
        Mirrorable.__init__(self, ControlledSer.TYP, ident, proxy)

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
        ser.append(self.getThrust())
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

    def deserialise(self, ser):
        (px, py, pz)=ControlledSer.vAssign(ser, ControlledSer._POS)
        (aw, ax, ay, az)=ControlledSer.qAssign(ser, ControlledSer._ATT)
        (vx, vy, vz)=ControlledSer.vAssign(ser, ControlledSer._VEL)
        return Mirrorable.deserialise(self, ser).setPos(Vector3(px,py,pz)).setAttitude(Quaternion(aw,ax,ay,az)).setVelocity(Vector3(vx,vy,vz)).setThrust(ser[ControlledSer._THRUST])
        
class Bot(Airfoil, ControlledSer):
    def __init__(self, ident=None):
        Airfoil.__init__(self)
        ControlledSer.__init__(self, ident)
			
class SerialisableFact:
    __OBJ_IDX,__TIME_IDX=range(2)

    def __init__(self, ctors):
        self.__notMine={}
        self.__objByType=[[],[],[]]
        try:
            assert len(self.__objByType)==SerialisableFact.getMaxType()+1
        except:
            print 'SerialisableFact.__init__. objByTypeField wrong size: '+str(self.__objByType)
        self.__mine={}
        self.__ctors=ctors

    @staticmethod
    def getMaxType():
        return 2

    def deserialiseAll(self, sers):
        deserialiseds=[]
        for serialised in sers:
            identifier=Mirrorable.deSerIdent(serialised)
            if identifier in self.__notMine:
                self.__notMine[identifier].deserialise(serialised)
            else:
                try:
                    typ=Mirrorable.deSerMeta(serialised, Mirrorable.TYPE)
                    if typ in self.__ctors:
                        print 'found new identifier: '+str(identifier)+' typ: '+str(typ)
                        obj = self.__ctors[typ](ident=identifier).deserialise(serialised)
                        self.__notMine[identifier] = obj
                        self.__objByType[typ].append(obj)
                    else:
                        assert False
                except AssertionError:
                    print >> sys.stderr, 'deserialiseAll. unrecognised typ: '+str(typ)+' '+str(serialised)

    def __contains__(self, ident):
        return ident in self.__notMine

    def getObj(self, ident):
        return self.__notMine[ident]

    def getTypeObjs(self, typ):
        try:
            assert typ<=SerialisableFact.getMaxType()
            return self.__objByType[typ]
        except AssertionError:
            print 'getTypeObjs. typ too large: '+str(typ)
        return []

class Client(Thread, Mirrorable):
    TYP=1
    __TOP_UP_LEN=32
    __LEN_LEN=10

    def initSys(self, ident):
        Sys.ID=Sys(ident)
        self.markChanged()
        return Sys.ID

    def __init__(self, ident=None, server='localhost', port=PORT):
        self.__server=server
        self.__port=port
        Mirrorable.__init__(self, self.TYP, ident, self)

    def local_init(self):
        Thread.__init__(self)
        Mirrorable.local_init(self)
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
        self.__ids=deque()
        self.__locked_serialised=dict()
        self.__outbox=deque()
        self.__out=''
        self.__in=''
        self.__fact=SerialisableFact({ ControlledSer.TYP: Bot, Client.TYP: Client, Sys.TYP: self.initSys })
        self.__lock=RLock()
        self.start()

    def addUpdated(self, mirrorable):
        try:
            #can't get any obj id if we don't have a sys id
            assert Sys.ID is not None
        except AssertionError:
            print >> sys.stderr, 'Client.addUpdated. System setup incomplete. Obj update lost'
            return

        #store mirrorable without needing to wait for lock
        if mirrorable.getId() not in self.__serialised:
            self.__ids.append(mirrorable.getId())
        self.__serialised[mirrorable.getId()]=mirrorable.serialise()

        if self.acquireLock() and Sys.ID is not None:
            while len(self.__ids)>0:
                unique=self.__ids.popleft()
                if unique not in self.__locked_serialised:
                    self.__outbox.append(unique)
                self.__locked_serialised[unique]=self.__serialised[unique][:]

            if len(self.__outbox)>0:
                self.send()

            self.__serialised=dict()
            self.releaseLock()

    def acquireLock(self, blocking=False):
        return self.__lock.acquire(blocking)

    def releaseLock(self):
        self.__lock.release()

    def __contains__(self, ident):
        return ident in self.__fact

    def getObj(self, ident):
        return self.__fact.getObj(ident)

    def getTypeObjs(self, typ):
        return self.__fact.getTypeObjs(typ)

    def send(self):
        unique=self.__outbox.popleft()
        obj=self.__locked_serialised[unique]
        del(self.__locked_serialised[unique])
        obj_s=obj[Mirrorable.META]+cPickle.dumps(obj[Mirrorable.META+1:])
        obj_len='%10s' %len(obj_s)
        self.__out+=obj_len
        self.__out+=obj_s
        try:
            assert len(self.__out)>0
            sent=self.__s.send(self.__out)
            self.__out=self.__out[sent:]
        except AssertionError:
            print >> sys.stderr, 'tried to send 0 bytes outbox: '+str(len(self.__outbox))


    def run(self):
        cur_len_in_s=''
        cur_len_in=0
        len_left=Client.__LEN_LEN
        sers=[]
        
        while(True):
            sleep_needed=False
            reads, writes, errs = select.select([self.__s], [], [], 60)
            if self.__s in reads:
                if self.acquireLock():
                    rec=self.__s.recv(4096)

                    while len(rec) != 0:
                        cur_len_in_s+=rec[:len_left]
                        if Client.__LEN_LEN - len(cur_len_in_s)==0: 
                            #we now know the length of the next obj
                            #print 'cur_len_in_s: '+cur_len_in_s
                            cur_len_in = int(cur_len_in_s)
                            self.__in+=rec[len_left:(len_left+cur_len_in)-len(self.__in)]
                            if len(self.__in)>=cur_len_in:
                                try:
                                    assert len(self.__in)==cur_len_in
                                    obj=[self.__in[:Mirrorable.META_SIZE]]
                                    obj.extend(cPickle.loads(self.__in[Mirrorable.META_SIZE:]))
                                    sers.append(obj)
                                    self.__in=''
                                    #print 'clearing cur_len_in_s'
                                    cur_len_in_s=''
                                except AssertionError:
                                    print >> sys.stderr, 'more in buffer than expected'
                                except ValueError:
                                    print >> sys.stderr, 'ValueError in Client.run. meta size: '+str(Mirrorable.META_SIZE)+' in: '+self.__in
                        #print 'removing up to '+str(len_left)+' + '+str(cur_len_in)+' chars from rec'
                        rec=rec[len_left+cur_len_in:]
                        len_left=Client.__LEN_LEN - len(cur_len_in_s)
                    self.__fact.deserialiseAll(sers)
                    sers[:]=[]
                    if self.getId() in self.__fact:
                        if not self.__fact.getObj(self.getId()).alive():
                            print 'quitting thread'
                            self.releaseLock()
                            self.__s.shutdown(socket.SHUT_RDWR)
                            self.__s.close()
                            print 'Client is quitting'
                            return
                    self.releaseLock()
                else:
                    sleep_needed=True
            if self.__s in writes:
                if self.acquireLock():
                    if len(self.__outbox)>0:
                        self.send()
                    else:
                        sleep_needed=True
                    self.releaseLock()
                else:
                    sleep_needed=True
            if sleep_needed:
                sleep(0)

class Sys(Mirrorable):
    ID=None
    TYP=2
    __NextInst=1

    @staticmethod
    def init(proxy):
	while True:
		if proxy.acquireLock():
			if Sys.ID is not None:
				proxy.releaseLock()
				break
			proxy.releaseLock()
		sleep(1)


    def __init__(self, ident=None):
        Mirrorable.__init__(self, Sys.TYP, ident)

    def local_init(self):
        self._ident=Sys.__NextInst
        Sys.__NextInst+=1

    def remote_init(self, ident):
        Mirrorable.remote_init(self, ident)
        ID=self

    def getSysId(self):
        return self._ident

    def markChanged(self):
        raise NotImplementedError

    def serialise(self):
        return [ ''.join([Mirrorable.int2Bytes(field, size) for (field, size) in zip([self.TYP, self._ident, 0, self._dead], self._SIZES)])]

class Server(Thread):
    def __init__(self, server='localhost', port=PORT, daemon=True):
        Thread.__init__(self)
        self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__s.setblocking(0)
        #self.__s.bind((gethostname(), port))
        self.__s.bind((server, port))
        self.__s.listen(5)
        self.__readers, self.__writers = ([], [])
        self.__serialisables={}
        self.__stopped=False
        self.daemon=daemon
        self.start()

    def qWrite(self, s, string):
        self.__serialisables[s]+=string
        if s not in self.__writers:
            self.__writers.append(s)

    def run(self):
        self.__running=True
        while True:
            try:
                reads, writes, errs = select.select(self.__readers+[self.__s], self.__writers, [], 60)
                for r in reads:
                    try:
                        if r is self.__s:
                            (client, address) = r.accept()
                            print 'accepted from '+str(address)
                            assert client not in self.__readers
                            self.__readers.append(client)
                            assert client not in self.__serialisables
                            assert client not in self.__writers
                            self.__serialisables[client]=''
                            system=Sys().serialise()
                            print 'system: '+str(system)+' '
                            system_s=system[Mirrorable.META]+cPickle.dumps(system[Mirrorable.META+1:])
                            self.qWrite(client, '%10s' %len(system_s)+system_s)
                        else:
                            d=r.recv(1024)
                            assert r in self.__serialisables
                            if not d:
                                # apparently this won't block
                                print 'shutting down client connection 0'
                                r.shutdown(socket.SHUT_RDWR)
                                r.close()
                                del self.__serialisables[r]
                                self.__readers.remove(r)
                                if r in self.__writers:
                                    self.__writers.remove(r)
                            else:
                                for reader in self.__readers:
                                    self.qWrite(reader, d)
                                    #print 'adding '+str(reader)' to writers. len: '+str(self.__serialisables[reader])
                    except AssertionError:
                        print >> sys.stderr, 'proxy.run. failed assertion on read'
                        print_exc()
                    except socket.error as (errNo, errStr):
                        print >> sys.stderr, "Server.run: exception on read. "+str((errNo,errStr))
                for w in writes:
                    try:
                        assert w in self.__serialisables 
                        assert len(self.__serialisables[w]) > 0
                        sent=w.send(self.__serialisables[w])
                        if not sent:
                            print 'shutting down client connection 1'
                            w.shutdown(socket.SHUT_RDWR)
                            w.close()
                            del self.__serialisables[w]
                            self.__writers.remove(w)
                            self.__readers.remove(w)
                        else:
                            self.__serialisables[w]=self.__serialisables[w][sent:]
                            if len(self.__serialisables[w])==0:
                                self.__writers.remove(w)
                    except AssertionError:
                        print >> sys.stderr, "proxy.run failed assertion on write"
                        print_exc()
                    except socket.error as (errNo, errStr):
                        print >> sys.stderr, "Server.run: exception on write. "+str((errNo,errStr))
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

