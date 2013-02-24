import manage as man

class SubjectSelector:
        def __init__(self, proxy, types, views):
                self.__proxy=proxy
                self.__types=types
                for v in views:
                        v.push_handlers(self)
                
        def on_subject_change(self, view, adjustment):
                view.link(self.pick(view, adjustment))

        def __get_subjects(self):
                planes=[ plane for plane in man.proxy.getTypesObjs(self.__types) ]
                ids=[ plane.getId() for plane in planes ]
                return (ids, planes)

        def pick(self, view, adj):
                (ids, subs)=self.__get_subjects()
                try:
                        print 'pick. ids: '+str(ids)
                        index=ids.index(view.getPlaneId())
                        index=(index+adj)%len(subs)
                        sub=subs[index]
                        return sub
                except ValueError:
                        if len(subs)>0:
                                sub=subs[0]
                                print 'SubjectSelector.exception'
                                return sub
                        else:
                                print 'SubjectSelector.exception. returning none '
                                return None
