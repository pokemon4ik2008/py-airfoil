from traceback import print_exc,print_stack
from thread import get_ident
from threading import RLock

class Scheduler:
    SCHEDS={}
    
    def __init__(self, block, receive=True):
        self.tasks=[]
        self.pending={}
        self.requests=[]
        tid=get_ident()
        if tid in Scheduler.SCHEDS:
            try:
                assert False
            except:
                print_stack()
        else:
            #block applied to the thread that run runs on
            self.__block=block
            if receive:
                self.__receiveLock=RLock()
            else:
                self.__receiveLock=None
            Scheduler.SCHEDS[tid]=self

    def acquire(self, block):
        try:
            assert self.__receiveLock is not None
            return self.__receiveLock.acquire(block)
        except:
            print_stack()
            
    def release(self):
        try:
            assert self.__receiveLock is not None
            self.__receiveLock.release()
        except:
            print_stack()

    def flush(self):
        #sends pending tasks / requests, only necessary for non-blocking Schedulers
        try:
            assert not self.__block
        except:
            print_stack()
        for tid in self.pending.keys():
            try:
                assert tid in SCHEDS
                receiver=SCHEDS[tid]
                receiver.acquire(self.__block)
                try:
                    (tasks, requests)=self.pending[tid]
                    receiver.tasks.extend(tasks)
                    receiver.requests.extend(requests)
                finally:
                    receiver.release()
            except:
                print_stack()
            del(self.pending[tid])

    def run(self):
        try:
            assert self.__receiveLock is not None
        except:
            print_stack()
        #receives tasks / requests
        if self.acquire(self.__block):
            try:
                #run on receiver thread
                for t in self.tasks:
                    try:
                        t()
                    except:
                        print_exc()
                        print_stack()
                self.tasks=[]

                for (r, orig_sender) in self.requests:
                    try:
                        handle=r()
                        orig_sender.scheduleTask(handler)
                    except:
                        print_stack()
                self.requests=[]
            finally:
                self.release()

    def schedule(self, item, dest_list, pending_idx):
        tid=get_ident()
        try:
            assert tid in Scheduler.SCHEDS
            sender=Scheduler.SCHEDS[tid]
            if self.acquire(sender.__block):
                try:
                    #sends tasks/requests, bypassing pending dict
                    dest_list.append(item)
                finally:
                    self.release()
            else:
                try:
                    assert not self.__block
                except:
                    print_stack()
                #adds to send pending dict
                if tid in sender.pending:
                    penders=(tasks, requests)=sender.pending[tid]
                else:
                    penders=([],[])
                penders[pending_idx].append(item)
        except:
            print_stack()

    def postTask(self, task):
        self.schedule(task, self.tasks, 0)

    def postRequest(self, req):
        self.schedule(task, self.requests, 1)
