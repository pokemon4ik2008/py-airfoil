import manage as man

class SubjectSelector:
        def __init__(self, proxy, types, views):
                self.__proxy=proxy
                self.__id=None
                self.__types=types
                for v in views:
                        v.push_handlers(self)
                
        def on_subject_change(self, view, adjustment):
                view.link(self.pick(adjustment))

        def __get_subjects(self):
                planes=[ plane for plane in man.proxy.getTypesObjs(self.__types) ]
                ids=[ plane.getId() for plane in planes ]
                return (ids, planes)

        def pick(self, adj):
                print 'SubjectSelector.pick'
                (ids, subs)=self.__get_subjects()
                try:
                        print 'SubjectSelector.pic. subs: '+str(subs)+' id: '+str(self.__id)
                        index=ids.index(self.__id)
                        index=(index+adj)%len(subs)
                        sub=subs[index]
                        self.__id=ids[index]
                        print 'SubjectSelector.pick: '+str(self.__id)
                        return sub
                except ValueError:
                        if len(subs)>0:
                                sub=subs[0]
                                self.__id=ids[0]
                                print 'SubjectSelector.exception: '+str(self.__id)
                                return sub
                        else:
                                self._id=None
                                print 'SubjectSelector.exception. returning none '
                                return None
