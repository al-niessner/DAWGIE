'''

COPYRIGHT:
Copyright (c) 2015-2023, California Institute of Technology ("Caltech").
U.S. Government sponsorship acknowledged.

All rights reserved.

LICENSE:
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

- Neither the name of Caltech nor its operating division, the Jet
Propulsion Laboratory, nor the names of its contributors may be used to
endorse or promote products derived from this software without specific prior
written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

NTR:
'''

import ae
import ae.feedback
import dawgie
import logging; log = logging.getLogger(__name__)

class Actor(dawgie.Task):
    def list(self): return [Command(), Control(), Model(), Sensor(),
                            SummingNode(), Output()]
    pass

class Command(dawgie.Algorithm):
    def __init__(self):
        dawgie.Algorithm.__init__(self)
        self.__command = StateVector('request', {'voltage':ae.Value(0,1)})
        self._version_ = dawgie.VERSION(1,0,0)
        return

    def name(self): return 'command'
    def previous(self): return []
    def run (self, ds, ps):
        self.__command['voltage'] = ae.Value(10,1)
        ds.update()
        return

    def state_vectors (self): return [self.__command]
    pass

class Control(dawgie.Algorithm):
    def __init__(self):
        dawgie.Algorithm.__init__(self)
        self.__base = SummingNode()
        self.__pid = StateVector('law', {'P':ae.Value(0.5,2),
                                         'I':ae.Value(0.3,2),
                                         'D':ae.Value(0,2)})
        self.__response = StateVector('response', {'accum':ae.Value(0,13),
                                                   'voltage':ae.Value(0,3)})
        self._version_ = dawgie.VERSION(1,0,0)
        return

    def name(self): return 'control'
    def previous(self): return [dawgie.ALG_REF(factory=ae.feedback.task,
                                               impl=self.__base),
                                dawgie.V_REF(factory=ae.feedback.task,
                                             impl=self, item=self.__response,
                                             feat='accum')]
    def run (self, ds, ps):
        accum = self.__response['accum'].array()
        signal = self.__base.state_vectors()[0]['voltage'].array()
        p = self.__pid['P'].array() * signal
        i = self.__pid['I'].array() * signal + accum
        self.__response['voltage'] = ae.Value(i+p,3)
        self.__response['accum'] = ae.Value(i,13)
        log.critical ('signal %f', signal)
        log.critical ('accum %f', self.__response['accum'].array())
        log.critical ('voltage %f', self.__response['voltage'].array())
        ds.update()
        return

    def state_vectors (self): return [self.__response, self.__pid]
    pass

class Model(dawgie.Algorithm):
    def __init__(self, ff=True):
        dawgie.Algorithm.__init__(self)
        self.__base = Control() if ff else None
        self.__model = StateVector('voltage', {'value':ae.Value(0,4)})
        self._version_ = dawgie.VERSION(1,0,0)
        return

    def name(self): return 'model'
    def previous(self):
        return [dawgie.V_REF(factory=ae.feedback.task,
                             impl=self.__base,
                             item=self.__base.sv_as_dict()['response'],
                             feat='voltage'),
                dawgie.V_REF(factory=ae.feedback.task, impl=self,
                             item=self.__model, feat='value')]
    def run (self, ds, ps):
        correction = self.__base.state_vectors()[0]['voltage'].array()
        state = self.__model['value'].array()
        output = int ((correction + state) * 10) / 10.0
        self.__model['value'] = ae.Value(output, [correction, state])
        log.critical ('reaction %f', self.__model['value'].array())
        ds.update()
        return

    def state_vectors (self): return [self.__model]
    pass

class Sensor(dawgie.Algorithm):
    def __init__(self):
        dawgie.Algorithm.__init__(self)
        self.__model = Model(False)
        self.__sensed = StateVector('measured', {'voltage':ae.Value(0,5)})
        self._version_ = dawgie.VERSION(1,0,0)
        return

    def feedback(self): return [dawgie.ALG_REF(factory=ae.feedback.task,
                                               impl=self.__model)]
    def name(self): return 'sensor'
    def previous(self): return []
    def run (self, ds, ps):
        state = self.__model.state_vectors()[0]['value']
        self.__sensed['voltage'] = ae.Value(-state.array(), state.uid())
        ds.update()
        return

    def state_vectors (self): return [self.__sensed]
    pass

class SummingNode(dawgie.Algorithm):
    def __init__(self):
        dawgie.Algorithm.__init__(self)
        self.__cmd = Command()
        self.__err = Sensor()
        self.__sum = StateVector('total', {'voltage':ae.Value(10,6)})
        self._version_ = dawgie.VERSION(1,0,0)
        return

    def name(self): return 'sum'
    def previous(self): return [dawgie.ALG_REF(factory=ae.feedback.task,
                                               impl=self.__cmd),
                                dawgie.ALG_REF(factory=ae.feedback.task,
                                               impl=self.__err)]
    def run (self, ds, ps):
        self.__sum['voltage'] = ae.Value(self.__cmd.state_vectors()[0]['voltage'].array() +
                                         self.__err.state_vectors()[0]['voltage'].array(), self.__err.state_vectors()[0]['voltage'].uid())
        log.critical ('Sum of error and command: %f',
                      self.__sum['voltage'].array())
        ds.update()
        return

    def state_vectors (self): return [self.__sum]
    pass

class Output(dawgie.Algorithm):
    def __init__(self):
        dawgie.Algorithm.__init__(self)
        self.__base = Model()
        self.__output = StateVector('actual', {'voltage':ae.Value(10,7)})
        self._version_ = dawgie.VERSION(1,0,0)
        return

    def name(self): return 'output'
    def previous(self): return [dawgie.ALG_REF(factory=ae.feedback.task,
                                               impl=self.__base)]
    def run (self, ds, ps):
        self.__output['voltage'] = ae.Value(self.__base.state_vectors()[0]['value'].array(),7)
        log.critical ('final reaction %f', self.__output['voltage'].array())
        ds.update()
        return

    def state_vectors (self): return [self.__output]
    pass

class StateVector(dawgie.StateVector):
    def __init__(self, name:str, start:{str:dawgie.Value}):
        dawgie.StateVector.__init__(self)
        self.__name = name
        self.update (start)
        self._version_ = dawgie.VERSION(1,0,0)
        return

    def name(self): return self.__name
    def view(self, visitor:dawgie.Visitor):
        for vn in sorted (self): visitor.add_primitive (self[vn].array(), vn)
        return
    pass
