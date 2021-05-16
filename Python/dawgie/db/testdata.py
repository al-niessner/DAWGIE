'''test data set for test13 and potenitally other uses

COPYRIGHT:
Copyright (c) 2015-2021, California Institute of Technology ("Caltech").
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

import dawgie

ASPECTS = []
DATASETS = []
KNOWNS = []
RUNID = 17
TARGET = 'test'
TIMELINES = []

class Fake(dawgie.Algorithm,dawgie.Analyzer,dawgie.Regression):
    def __init__(self, name, bug):
        self._version_ = dawgie.VERSION(1,1,bug)
        self.myname = name
        self.sv = []
        pass
    def name(self): return self.myname
    def previous(self): return []
    # pylint: disable=arguments-differ,unused-argument
    def run(self, *args, **kwds): return
    # pylint: enable=arguments-differ,unused-argument
    def state_vectors(self): return self.sv
    def traits(self): return []
    def variables(self): return []
    pass

class Analysis(dawgie.Analysis):
    def __init__(self, name, ps_hint, runid):
        dawgie.Analysis.__init__(self, name, ps_hint, runid)
        self.mylist = []
        return
    def list(self): return self.mylist
    pass

class Regress(dawgie.Regress):
    def __init__(self, name, ps_hint, target):
        dawgie.Regress.__init__ (self, name, ps_hint, target)
        self.mylist = []
        return
    def list(self): return self.mylist
    pass

class StateVector(dawgie.StateVector):
    def __init__(self, name):
        self.myname = name
        self._version_ = dawgie.VERSION(1,2,3)
        return
    def name(self): return self.myname
    def view(self, visitor): return
    pass

class Task(dawgie.Task):
    def __init__(self, name, ps_hint, runid, target='__all__'):
        dawgie.Task.__init__(self, name, ps_hint, runid, target)
        self.mylist = []
        return
    def list(self): return self.mylist
    pass

class Value(dawgie.Value):
    def __init__(self, val):
        self._version_ = dawgie.VERSION(5,6,7)
        self.val = val
        return
    def features(self): return []
    def get(self): return self.val
    def set(self, val): self.val = val
    pass

for tsk_idx in range(13):
    rem = tsk_idx % 3
    tidx = tsk_idx // 3

    if rem == 0: tsk = Analysis('Analysis_{:02d}'.format (tidx), 0, RUNID)
    if rem == 1: tsk = Regress('Regress_{:02d}'.format (tidx), 0, TARGET)
    if rem == 2: tsk = Task('Task_{:02d}'.format (tidx), 0, RUNID, TARGET)

    for ver_idx in range(3):
        for alg_idx in range(11):
            if rem == 0: base = 'Analyzer'
            if rem == 1: base = 'Regression'
            if rem == 2: base = 'Task'

            base += '_{:02d}'
            alg = Fake(base.format (alg_idx), ver_idx)
            tsk.mylist.append (alg)
            for svn_idx in range(7):
                sv = StateVector('StateVector_{:02d}'.format(svn_idx))
                alg.sv.append (sv)
                for val_idx in range(5):
                    vn = 'Value_{:02d}'.format (val_idx)
                    sv[vn] = Value(-(len(KNOWNS)+1))
                    KNOWNS.append ((tsk, alg, sv, vn, sv[vn]))
                    pass
                pass
            pass
        pass

    if rem == 0: ASPECTS.append ((tsk, alg))
    if rem == 1: TIMELINES.append ((tsk, alg))
    if rem == 2: DATASETS.append ((TARGET, tsk, alg))
    pass
