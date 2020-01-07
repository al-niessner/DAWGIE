'''

COPYRIGHT:
Copyright (c) 2015-2020, California Institute of Technology ("Caltech").
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
import ae.network
import ae.network.bot
import dawgie
import os
import pickle
import tempfile

class Actor(dawgie.Task):
    def list(self): return [Engine()]
    pass

class Engine(dawgie.Algorithm):
    def __init__(self):
        dawgie.Algorithm.__init__(self)
        self.__base = ae.network.bot.Engine()
        self.__dirty = ae.StateVector()
        self.__noise = ae.network.bot.Analyzer()
        self._version_ = dawgie.VERSION(1,0,0)
        return

    def name(self): return 'engine'
    def previous(self): return [dawgie.ALG_REF(factory=ae.network.analysis,
                                               impl=self.__noise),
                                dawgie.ALG_REF(factory=ae.network.task,
                                               impl=self.__base)]

    def run (self, ds, ps):
        base = self.__base.sv_as_dict()['test']['image'].array()
        dirt = self.__noise.sv_as_dict()['test']['image'].array()
        for _i in range (10):
            fid,fn = tempfile.mkstemp()
            os.close (fid)
            with open (fn, 'bw') as f: pickle.dump (base, f)
            os.unlink (fn)
            pass
        self.__dirty['image'] = ae.Value(array=base+dirt)
        ds.update()
        return

    def state_vectors (self): return [self.__dirty]
    pass
