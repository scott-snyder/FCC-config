#
# File: python/FCC_config.ComponentAccumulator.py
# Author: scott snyder <snyder@bnl.gov>
# Date: Feb, 2026
# Purpose: ComponentAccumulator-style configuration for key4hep.
#
# This module provides a ComponentAccumulator class for structured
# configuration, along the lines of ATLAS (see
# https://doi.org/10.1051/epjconf/201921405015 and section 3.2 of
# https://doi.org/10.1140/epjc/s10052-024-13701-w).
# Only the bare minimum required to try this out is implemented at this point;
# in particular, component de-duplication is not implemented (except for an
# ad-hoc facility for Services, see below).  More functionality from ATLAS
# can be added as needed.
#
# key4hep configurations have tended to be monolithic python scripts.
# For any significant configuration, maintaining this gets tedious and
# error-prone, and results in large amounts of duplicated configuration code,
# making it complicated to introduce changes in how components get configured.
#
# In this model, components are configured via configuration functions,
# which ideally are provided via by the library defining the components.
# Each function creates Gaudi Configurables for one component or a set of
# closely related components and returns them via a ComponentAccumulator object.
# These functions have no access to global state, taking all their information
# via arguments; however, their first argument is conventionally a flags
# object conveying information about what sort of configuration is desired.
#
# 

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
        for sname, s in self._svcs.items():
            cnv = getattr (s, 'convertTo', None)
            if cnv and callable(cnv):
                s = cnv(s)
            extSvc.append(s)

        return self.__reset()
