def _mergeSvc (old, new):
    mergef = getattr (new, 'mergeTo', None)
    if not mergef or not callable(mergef):
        return False
    return mergef (old)


class ComponentAccumulator:
    def __init__ (self):
        return self.__reset()
    def __reset (self):
        self._algSeq = []
        self._algs = {}
        self._svcs = {}
        return
    def addAlg (self, a):
        if a.name() in self._algs:
            print ('ERROR: Duplicate algorithm', a.name())
            assert 0
        self._algSeq.append(a)
        self._algs[a.name()] = a
        return
    def algs (self):
        return self._algSeq
    def addSvc (self, s):
        if s.name() in self._svcs:
            if not _mergeSvc (self._svcs[s.name()], s):
                print ('ERROR: Unmergable duplicate service', s.name())
                assert 0
        else:
            self._svcs[s.name()] = s
        return
    def svcs (self):
        return self._svcs.values()

    def merge (self, other):
        for a in other.algs():
            self.addAlg (a)
        for s in other.svcs():
            self.addSvc (s)
        return

    def toVars (self, topAlg, extSvc):
        for a in topAlg:
            if a.name() in self._algs:
                print ('ERROR: Duplicate algorithm', a.name())
                assert 0
        topAlg += self.algs()

        for s in extSvc:
            sname = s if isinstance(s, str) else s.name()
            if sname in self._svcs:
                if _mergeSvc (s, self._svcs[sname]):
                    del self._svcs[sname]
                else:
                    print ('ERROR: Unmergable duplicate service', sname)
                    assert 0
        for sname, s in self._svcs:
            cnv = getattr (s, 'convertTo', None)
            if cnv and callable(cnv):
                s = cnv(s)
            extSvc.append(s)

        return self.__reset()
