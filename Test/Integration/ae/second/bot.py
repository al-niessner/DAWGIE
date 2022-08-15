'''The algorithm engine for touching the local disk

COPYRIGHT:
Copyright (c) 2015-2022, California Institute of Technology ("Caltech").
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
import ae.prime
import ae.prime.bot
import dawgie
import numpy.random

class Actor(dawgie.Task):
    def list(self): return [Engine()]
    pass

class Engine(dawgie.Algorithm):
    def __init__(self):
        dawgie.Algorithm.__init__(self)
        self.__prime = ae.prime.bot.Engine()
        self.__sv = ae.StateVector()
        self.__sv['e'] = ae.Value (1.0, 0)
        self.__sv['f'] = ae.Value (1.0, 0)
        self._version_ = dawgie.VERSION(1,0,0)
        return

    def name(self): return 'engine'
    def previous(self): return [dawgie.V_REF(factory=ae.prime.task,
                                             impl=self.__prime,
                                             item=self.__prime.state_vectors()[0],
                                             feat='c')]

    def run (self, ds, ps):
        self.__sv['e'] = ae.Value (numpy.random.rand() + self.__prime.state_vectors()[0]['c'].value(), 0x0011)
        self.__sv['f'] = ae.Value (numpy.random.rand() * self.__prime.state_vectors()[0]['c'].value(), 0x0012)
        ds.update()
        return

    def state_vectors (self): return [self.__sv]
    pass
