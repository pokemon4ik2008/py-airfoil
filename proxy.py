from airfoil import Airfoil
import cPickle
from collections import deque
from euclid import Quaternion, Vector3
import manage
from Queue import LifoQueue
import re
import select
import socket
from socket import gethostname, gethostbyname
from subprocess import Popen, PIPE
import sys
from threading import Condition, RLock, Thread
from time import sleep, time
from traceback import print_exc

PORT=8124
LEN_LEN=4

def getLocalIP():
    addr = socket.gethostbyname(socket.gethostname())
    if addr.startswith('127'):
        try:
            import commands
            return commands.getoutput("hostname -I").split('\n')[0].strip()     
        except:
            print_exc()
    return addr
        
def int2Bytes(i, size):
    s=''
    for idx in range(size):
        s+=chr((i >> (idx*8)) & 0xff)
    return s

def bytes2Int(s):
    i=0
    for idx in range(len(s)):
       i |= ord(s[idx]) << (idx*8) 
    return i

def toHexStr(string):
    bytes=''
    for c in string:
        bytes+='%02x'%ord(c)
    return bytes

class Mirrorable:
    META=0
    __INDEXES=[TYPE, IDENT, SYS, FLAGS]=range(4)
    _SIZES = [2, 2, 2, 1]
    META_SIZE=sum(_SIZES)
    SHIFTS = [sum(_SIZES[:i]) for i in __INDEXES]
    __InstCount = 0
    _DEAD_FLAG=0x1
    _DROPPABLE_FLAG=0x2

    def __init__(self, typ, ident=None, proxy=None, uniq=None):
        self._proxy=proxy
        try:
            assert typ<=SerialisableFact.getMaxType()
        except AssertionError:
            print >> sys.stderr, 'Mirrorable.__init__. typ too large: '+str(typ)
        self.__typ=typ
        self._flags=0
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
        return (self._flags & self._DEAD_FLAG)==0

    def markDead(self, dead=True):
        if dead:
            self._flags |= self._DEAD_FLAG
        else:
            self._flags &= ~(self._DEAD_FLAG)

    def serialise(self):
        return [ ''.join([int2Bytes(field, size) for (field, size) in zip([self.__typ, self._ident, Sys.ID.getSysId(), self._flags], self._SIZES)])]
        #return [self.__typ, self._ident, self.__dead]

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

    def deserialise(self, serialised):
        flags=Mirrorable.deSerMeta(serialised, self.FLAGS)
        self._flags=flags
        return self

class ControlledSer(Mirrorable):
    TYP=0
    [ _POS,_,_, _ATT,_,_,_, _VEL,_,_, _THRUST ] = range(Mirrorable.META+1, Mirrorable.META+12)

    def __init__(self, ident=None, proxy=None):
        Mirrorable.__init__(self, ControlledSer.TYP, ident, proxy)

    def local_init(self):
        Mirrorable.local_init(self)
        self._flags |= self._DROPPABLE_FLAG

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

    @staticmethod
    def loads(obj_str):
        meta=obj_str[:Mirrorable.META_SIZE]
        obj=[meta]
        obj.extend(cPickle.loads(obj_str[Mirrorable.META_SIZE:]))
        return obj

    def deserialiseAll(self, sers):
        deserialiseds=[]
        for identifier in sers:
            serialised=SerialisableFact.loads(sers[identifier])
            #print 'deserialiseAll. identifier '+str(identifier)
            if identifier in self.__notMine:
                self.__notMine[identifier].deserialise(serialised)
            else:
                try:
                    typ=Mirrorable.deSerMeta(serialised, Mirrorable.TYPE)
                    if typ in self.__ctors:
                        #print 'found new identifier: '+str(identifier)+' typ: '+str(typ)
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
     TYP=1
     __TOP_UP_LEN=32

     def initSys(self, ident):
         Sys.ID=Sys(ident)
         self.markChanged()
         return Sys.ID

     def __init__(self, ident=None, server=getLocalIP(), port=PORT):
         self.__server=server
         self.__port=port
         Mirrorable.__init__(self, self.TYP, ident, self)

     def local_init(self):
         Thread.__init__(self)
         Mirrorable.local_init(self)
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
         self.__fact=SerialisableFact({ ControlledSer.TYP: Bot, Client.TYP: Client, Sys.TYP: self.initSys })
         self.__lock=RLock()
         self.__open=True
         self.daemon=True
         self.start()

     def attemptSendAll(self):
         if self.acquireLock() and Sys.ID is not None:
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
         else:
             if not self.alive():
                 print 'no lock so not sending tail yet'
         return False

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
         self.attemptSendAll()

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
         try:
             assert len(self.__out)>0
             sent=self.__s.send(self.__out)
             self.__out=self.__out[sent:]
         except AssertionError:
             print >> sys.stderr, 'tried to send 0 bytes outbox: '+str(len(self.__outbox))

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
                 if not self.alive():
                     print 'after select. proxy is dead'
                 if self.__s in reads:
                     if self.acquireLock():
                         read_now=self.__s.recv(4096)
                         if read_now=='':
                             self.markDead()
                             self.releaseLock()
                             self.__open=False
                             break
                         #print 'Client.run: len read: '+str(len(rec))
                         rec=read(self.__s, rec+read_now, self.addSerialisables, lambda sock: None)
                         self.__fact.deserialiseAll(self.__sers)
                         if self.getId() in self.__fact and not self.getObj(self.getId()).alive():
                             print 'Client.run. closing socket'
                             self.releaseLock()
                             self.__open=False
                             break
                         self.__sers={}
                         self.releaseLock()
                     else:
                         sleep_needed=True
                 if self.__s in writes:
                     if not self.alive():
                         print 'after select. proxy is dead and socket is writeable'
                     if self.acquireLock():
                         if not self.alive():
                             print 'after select. proxy is dead and socket is writeable and we have the lock'
                         if len(self.__outbox)>0:
                             if not self.alive():
                                 print 'after select. proxy is dead and socket is writeable and we have the lock and we have something to send'
                             self.send()
                         else:
                             sleep_needed=True
                         self.releaseLock()
                     else:
                         sleep_needed=True
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
    ID=None
    TYP=2
    __NextInst=1

    @staticmethod
    def init(proxy):
        while manage.proxy.alive():
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
        return [ ''.join([int2Bytes(field, size) for (field, size) in zip([self.TYP, self._ident, 0, self._flags], self._SIZES)])]

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

        if (flags & Mirrorable._DROPPABLE_FLAG)!=Mirrorable._DROPPABLE_FLAG:
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
                                (client, address) = r.accept()
                                print 'accepted from '+str(address)
                                assert client not in self.__readers
                                self.__readers.append(client)
                                assert client not in self.__serialisables
                                assert client not in self.__writers
                                self.__serialisables[client]=''
                                system=Sys().serialise()
                                print 'system: '+str(system)
                                system_s=system[Mirrorable.META]+cPickle.dumps(system[Mirrorable.META+1:])
                                #print 'system: serialised. '+toHexStr(system_s)
                                self.qWrite(client, int2Bytes(len(system_s), LEN_LEN)+system_s)
                                #print 'server.run. len '+str(len(system_s))+' '+toHexStr(int2Bytes(len(system_s), LEN_LEN))
                                #self.qWrite(client, '%10s' %len(system_s)+system_s)
                                self.__in[client]=''
                                self.__accepted_clients=True
                            else:
                                self.__outQs[r]=[]
                                self.__outs[r]={}
                                read_now=r.recv(4096)
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
