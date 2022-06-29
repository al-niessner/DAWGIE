'''

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
import ae.network
import dawgie
import dawgie.db
import numpy
import os
import tempfile
import urllib.request

class Actor(dawgie.Analysis):
    def list(self)->[dawgie.Analyzer]: return [Analyzer()]
    pass

class Agent(dawgie.Task):
    def list(self)->[dawgie.Task]: return [Engine()]
    pass

class Analyzer(dawgie.Analyzer):
    def __init__(self):
        dawgie.Analyzer.__init__(self)
        self.__noise = ae.StateVector()
        self._version_ = dawgie.VERSION(1,0,0)
        return

    def name(self): return 'analyzer'

    def run(self, aspects):
        # pylint: disable=protected-access
        self.__noise['image'] = ae.Value((numpy.random.rand (4000,4000)-.5)*.1)
        fid,tn = tempfile.mkstemp()
        os.close (fid)
        os.unlink (tn)
        dawgie.db.connect (Engine(), aspects.ds()._bot(), tn).load()
        aspects.ds().update()
        return

    def state_vectors(self): return [self.__noise]
    def traits(self): return []
    pass

class Engine(dawgie.Algorithm):
    def __init__(self):
        dawgie.Algorithm.__init__(self)
        self.__base = Analyzer()
        self.__image = ae.StateVector()
        self._version_ = dawgie.VERSION(1,0,0)
        return

    def name(self): return 'engine'
    def previous(self): return [dawgie.ALG_REF(factory=ae.network.analysis,
                                               impl=self.__base)]

    def run (self, ds, ps):
        shape = self.__base.sv_as_dict()['test']['image'].array().shape
        image = numpy.empty (shape)
        for r in range (shape[0]):
            for c in range (shape[1]):
                image[r,c] = numpy.sin(r/700) * numpy.cos(c/500 - numpy.pi/4)
                pass
            pass
        url = "https://github.com/OpenExoplanetCatalogue/oec_gzip/raw/master/systems.xml.gz"
        with urllib.request.urlopen (url) as link: link.read()
        self.__image['image'] = ae.Value(image)
        ds.update()
        return

    def state_vectors(self): return [self.__image]
    pass
