from airfoil import Airfoil
import cPickle
from collections import deque
from euclid import Vector3
from Queue import LifoQueue
import select
import socket
import sys
from threading import Condition, RLock, Thread
from time import sleep

class Mirrorable:
    [TYPE, IDENT, _DEAD ] = range(3)
    __InstCount = 0

    def __init__(self, typ, ident=None, proxy=None, uniq=None):
        self.__proxy=proxy
        self.__typ=typ
        self.__dead=False
        if ident is None:
            self.local_init()
        else:
            self.__ident=ident

    def local_init(self):
        self.__ident=Mirrorable.__InstCount
        Mirrorable.__InstCount+=1
        
    def getId(self):
        return self.__ident

    def markChanged(self):
        if self.__proxy is None:
            raise NotImplementedError
        self.__proxy.addUpdated(self)
        return self.alive()

    #def getUnique(self):
    #    return (self.__typ, self.getId())    

    def alive(self):
        return not self.__dead

    def markDead(self, dead=True):
        self.__dead=dead

    def serialise(self):
        return [self.__typ, self.__ident, self.__dead]

    def deserialise(self, serialised):
        if serialised[Mirrorable._DEAD]:
            print 'deser. dead: '+str(serialised)
        self.markDead(serialised[Mirrorable._DEAD])
        return self

class ControlledSer(Mirrorable):
    TYP=1
    [ _POS, _ATT, _VEL, _THRUST ] = range(Mirrorable._DEAD+1, Mirrorable._DEAD+5)

    def __init__(self, ident=None, proxy=None):
        Mirrorable.__init__(self, ControlledSer.TYP, ident, proxy)

    def serialise(self):
        ser=Mirrorable.serialise(self)
        p=self.getPos()
        ser.append(p.copy())
        a=self.getAttitude()
        ser.append(a.copy())
        v=self.getVelocity()
        ser.append(v.copy())
        ser.append(self.getThrust())
        return ser

    def deserialise(self, ser):
        return Mirrorable.deserialise(self, ser).setPos(ser[ControlledSer._POS]).setAttitude(ser[ControlledSer._ATT]).setVelocity(ser[ControlledSer._VEL]).setThrust(ser[ControlledSer._THRUST])
        
class Bot(Airfoil, ControlledSer):
    def __init__(self, ident=None):
        Airfoil.__init__(self)
        ControlledSer.__init__(self, ident)
			
class SerialisableFact:
    __OBJ_IDX,__TIME_IDX=range(2)

    def __init__(self, serialisables):
        self.__notMine=dict()
        self.__mine=dict()
        self.__heapq=[]
        for serialisable in serialisables:
            self.__notMine[serialisable.getId()]=serialisable

    def addUpdated(self, mirrorable=None):
        pass

    def deserialiseAll(self, sers):
        deserialiseds=[]
        for serialised in sers:
            identifier=serialised[Mirrorable.IDENT]
            if identifier in self.__notMine:
                self.__notMine[identifier].deserialise(serialised)
            else:
                try:
                    if serialised[Mirrorable.TYPE] in CTORS:
                        self.__notMine[identifier] = CTORS[serialised[Mirrorable.TYPE]](ident=identifier).deserialise(serialised)
                    else:
                        assert False
                except AssertionError:
                    print >> sys.stderr, 'deserialiseAll. unrecognised typ: '+str(typ)

    def __contains__(self, ident):
        return ident in self.__notMine

    def getObj(self, ident):
        return self.__notMine[ident]

class Client(SerialisableFact, Thread, Mirrorable):
    TYP=2

    __TOP_UP_LEN=32
    __LEN_LEN=10

    def __init__(self, ident=None, serialisables=[], server='localhost', port=8123):
        self.__server=server
        self.__port=port
        self.__serialisables=serialisables
        Mirrorable.__init__(self, self.TYP, ident, self)

    def local_init(self):
        Thread.__init__(self)
        SerialisableFact.__init__(self, self.__serialisables)
        self.__serialisables=None
        Mirrorable.local_init(self)
        self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__s.setblocking(0)
        try:
            self.__s.connect((self.__server, self.__port))
        except socket.error as (errNo, errStr):
            if errNo==115:
                #EINPROGRESS
                pass
            else:
                print >> sys.stderr, "Client.__init__ failed to connect: "+errNo+" "+errStr
        self.__serialised=dict()
        self.__ids=deque()
        self.__locked_serialised=dict()
        self.__outbox=deque()
        self.__out=''
        self.__in=''
        self.__lock=RLock()
        self.start()

    def addUpdated(self, mirrorable):
        #store mirrorable without needing to wait for lock
        if mirrorable.getId() not in self.__serialised:
            self.__ids.append(mirrorable.getId())
        self.__serialised[mirrorable.getId()]=mirrorable.serialise()

        if self.acquireLock():
            while len(self.__ids)>0:
                unique=self.__ids.popleft()
                if unique not in self.__locked_serialised:
                    self.__outbox.append(unique)
                self.__locked_serialised[unique]=self.__serialised[unique][:]

            self.__serialised=dict()
            self.releaseLock()

    def acquireLock(self):
        return self.__lock.acquire(blocking=False)

    def releaseLock(self):
        self.__lock.release()

    def run(self):
        cur_len_in_s=''
        cur_len_in=0
        len_left=Client.__LEN_LEN
        sers=[]

        # set up connection state
        self.markChanged()
        
        while(True):
            reads, writes, errs = select.select([self.__s], [self.__s], [], 60)
            if self.acquireLock():
                if self.__s in reads:
                    rec=self.__s.recv(4096)
                    #print 'rec: '+rec

                    while len(rec) != 0:
                        cur_len_in_s+=rec[:len_left]
                        if Client.__LEN_LEN - len(cur_len_in_s)==0: 
                            #we now know the length of the next obj
                            #print 'cur_len_in_s: '+cur_len_in_s
                            cur_len_in = int(cur_len_in_s)
                            self.__in+=rec[len_left:len_left+cur_len_in]
                            if len(self.__in)>=cur_len_in:
                                try:
                                    assert len(self.__in)==cur_len_in
                                    sers.append(cPickle.loads(self.__in))
                                    self.__in=''
                                    #print 'clearing cur_len_in_s'
                                    cur_len_in_s=''
                                except AssertionError:
                                    print >> sys.stderr, 'more in buffer than expected'
                        #print 'removing up to '+str(len_left)+' + '+str(cur_len_in)+' chars from rec'
                        rec=rec[len_left+cur_len_in:]
                        len_left=Client.__LEN_LEN - len(cur_len_in_s)
                    self.deserialiseAll(sers)
                    sers[:]=[]
                    if self.getId() in self:
                        if not self.getObj(self.getId()).alive():
                            print 'quitting thread'
                            break

                if self.__s in writes:
                    if len(self.__outbox)>0:
                         unique=self.__outbox.popleft()
                         obj=self.__locked_serialised[unique]
                         del(self.__locked_serialised[unique])
                         obj_s=cPickle.dumps(obj)
                         obj_len='%10s' %len(obj_s)
                         self.__out+=obj_len
                         self.__out+=obj_s
                         try:
                             assert len(self.__out)>0
                             sent=self.__s.send(self.__out)
                             self.__out=self.__out[sent:]
                         except AssertionError:
                             print >> sys.stderr, 'tried to send 0 bytes outbox: '+str(len(self.__outbox))

                self.releaseLock()
            else:
                sleep(0)
        self.releaseLock()
        print 'Client is quitting'

class Server(Thread):
    def __init__(self, port=8123):
        Thread.__init__(self)
        self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__s.setblocking(0)
        #self.__s.bind((gethostname(), port))
        self.__s.bind(('localhost', port))
        self.__s.listen(5)
        self.__readers, self.__writers = ([], [])
        self.__serialisables={}
        self.__stopped=False
        self.daemon=True
        self.start()

    def run(self):
        while(True):
            try:
                reads, writes, errs = select.select(self.__readers+[self.__s], self.__writers, [], 60)
                for r in reads:
                    try:
                        if r is self.__s:
                            (client, address) = r.accept()
                            assert client not in self.__readers
                            self.__readers.append(client)
                            assert client not in self.__serialisables
                            self.__serialisables[client]=''
                            assert client not in self.__writers
                        else:
                            d=r.recv(1024)
                            assert r in self.__serialisables
                            if not d:
                                # apparently this won't block
                                r.shutdown(socket.SHUT_RDWR)
                                r.close()
                                del self.__serialisables[r]
                                self.__readers.remove(r)
                                if r in self.__writers:
                                    self.__writers.remove(r)
                            else:
                                for reader in self.__readers:
                                    self.__serialisables[reader]+=d
                                    if reader not in self.__writers:
                                        self.__writers.append(r)
                    except AssertionError:
                        print >> sys.stderr, 'proxy.run. failed assertion on read'
                    
                for w in writes:
                    try:
                        assert w in self.__serialisables and len(self.__serialisables[w]) > 0
                        sent=w.send(self.__serialisables[w])
                        if not sent:
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

CTORS = { ControlledSer.TYP: Bot, Client.TYP: Client }
