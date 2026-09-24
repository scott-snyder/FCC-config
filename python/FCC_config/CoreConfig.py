from .ComponentAccumulator import ComponentAccumulator
import Configurables as C
from k4FWCore import IOSvc as IO


class IOSvc:
    def __init__ (self, name, Input, Output, outputCommands = []):
        self._name = name
        self.Input = Input
        self.Output = Output
        self.outputCommands = outputCommands
        return
    def name (self):
        return self._name

    def mergeTo (self, old):
        if type(old) is not IOSvc and type(old) is not IO:
            print ('ERROR: Bad type for merging IOSvc:', type(old))
            return False
        if self.Input != old.Input:
            print (f'ERROR: merging {old.name()}; Input mismatch: {old.Input} versus {self.Input}')
            return False
        if self.Output != old.Output:
            print (f'ERROR: merging {old.name()}; Output mismatch: {old.Output} versus {self.Output}')
            return False
        for c in self.outputCommands:
            if c not in old.outputCommands:
                old.outputCommands.append (c)
        return True


    def convertTo (self):
        return IO (name, Input=self.Input, Output=self.Output,
                   outputCommands = self.outputCommands)


def IOSvcCfg (flags, name='IOSvc', drop=[], keep=[]):
    ca = ComponentAccumulator()
    ca.addSvc (IOSvc (name,
                      Input = flags.IO.inputFile,
                      Output = flags.IO.outputFile,
                      outputCommands = ['drop ' + x for x in drop] +
                      ['keep ' + x for x in keep]))
    return ca

