'''Argument helpers for the CLI

--
COPYRIGHT:
Copyright (c) 2015-2024, California Institute of Technology ("Caltech").
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

NTR: 49811
'''

import dawgie
from dawgie import ALG_REF,SV_REF,V_REF,Distribution

class Specific:
    def __init__ (self, real, specific:dawgie.StateVector):
        self.__name = f'{real.name()}<{specific.name()}>'
        self.__real = real
        self.__spec = specific
        return

    def name(self)->str: return self.__name

    @property
    def real(self): return self.__real

    def state_vectors(self)->'[StateVector]':
        return [self.__spec] + self.real.state_vectors()
    pass

class SpecificAlgorithm(Specific,dawgie.Algorithm):
    def __init__(self, real:dawgie.Algorithm, specific:dawgie.StateVector):
        Specific.__init__(self, real, specific)
        return
    def abort(self)->bool: return self.real.abort()
    def feedback(self)->[SV_REF, V_REF]: return self.real.feedback()
    def previous(self)->[SV_REF, V_REF]: return self.real.previous()
    def run(self, ds, ps): self.real.run (ds, ps)
    def sv_as_dict(self)->'{str:StateVector}': return self.real.sv_as_dict()
    def where(self)->Distribution: return self.real.where()
    pass

class SpecificAnalyzer(Specific,dawgie.Analyzer):
    def __init__(self, real:dawgie.Analyzer, specific:dawgie.StateVector):
        Specific.__init__(self, real, specific)
        return
    def abort(self)->bool: return self.real.abort()
    def feedback(self)->[SV_REF, V_REF]: self.real.feedback()
    def run (self, aspects:'Aspect')->None: self.real.run(aspects)
    def sv_as_dict(self)->'{str:StateVector}': return self.real.sv_as_dict()
    def traits(self)->[ALG_REF, SV_REF, V_REF]: return self.real.traits()
    def where(self)->Distribution: return self.real.where()
    pass

class SpecificRegression(Specific,dawgie.Regression):
    def __init__(self, real:dawgie.Regression, specific:dawgie.StateVector):
        Specific.__init__(self, real, specific)
        return
    def abort(self)->bool: return self.real.abort()
    def feedback(self)->[SV_REF, V_REF]: return self.real.feedback()
    def run (self, ps:int, timeline:'Timeline')->None:
        self.real.run(ps, timeline)
    def sv_as_dict(self)->'{str:StateVector}':
        return self.real.sv_as_dict()
    def variables(self)->[ALG_REF, SV_REF, V_REF]: return self.real.variables()
    def where(self)->Distribution: return self.real.where()
    pass

def specify (general:dawgie.Generic)->[Specific]:
    if isinstance (general, dawgie.Algorithm): cls = SpecificAlgorithm
    elif isinstance (general, dawgie.Analyzer): cls = SpecificAnalyzer
    elif isinstance (general, dawgie.Regression): cls = SpecificRegression
    else: raise TypeError('general must be an instance of dawgie.Generic and dawigie.Algorith/Analyzer/Regression.')
    return [cls(general,sv) for sv in general.specifics]
