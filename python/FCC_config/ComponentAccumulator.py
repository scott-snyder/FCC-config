class ComponentAccumulator:
    def __init__ (self):
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
            print ('ERROR: Duplicate service', s.name())
            assert 0
        self._svcs[s.name()] = s
        return
    def svcs (self):
        return self._svcs.values()

    def merge (self, other):
        for a in other.algs():
            self.addAlg (a)
        for s in other.svcs():
            self.addSvs (s)
        return
