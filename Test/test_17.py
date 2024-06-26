'''

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

NTR:
'''

import dawgie
import unittest
import unittest.mock

class NCAlg(dawgie.Algorithm):
    def name(self): return 'NCAlg'
class NCAsp(dawgie.Analyzer):
    def name(self): return 'NCAsp'
class NCReg(dawgie.Regression):
    def name(self): return 'NCReg'

class WCAlg(dawgie.Algorithm):
    fullrepr = None
    def name(self): return 'WCAlg'
    def previous(self): return []
    def run(self, *args): WCAlg.fullrepr = repr(self)
class WCAsp(dawgie.Analyzer):
    fullrepr = None
    def name(self): return 'WCAsp'
    def run(self, *args): WCAsp.fullrepr = repr(self)
    def traits(self): return []
class WCReg(dawgie.Regression):
    fullrepr = None
    def name(self): return 'WCReg'
    def run(self, *args): WCReg.fullrepr = repr(self)
    def variables(self): return []
class Analysis(dawgie.Analysis):
    def list(self): return [WCAsp()]
class Aspect(dawgie.Aspect):
    def collect (*args, **kwds): return
    def ds(*args, **kwds): return None
class Regress(dawgie.Regress):
    def list(self): return [WCReg()]
class Task(dawgie.Task):
    def _make_ds(self, alg): return None
    def list(self): return [WCAlg()]
class Timeline(dawgie.Timeline):
    def ds(*args,**kwds): return None
    def recede (*args,**kwds): return

class Repr(unittest.TestCase):
    def test_no_caller(self):
        self.assertEqual(repr(NCAlg()), 'NCAlg')
        self.assertEqual(repr(NCAsp()), 'NCAsp')
        self.assertEqual(repr(NCReg()), 'NCReg')
    def test_with_caller(self):
        with unittest.mock.patch ('dawgie.db.gather', gather):
            Analysis('meditate', 2, 37).do()
        with unittest.mock.patch ('dawgie.db.retreat', retreat):
            Regress('pit', 2, 'cherry').do()
        Task('seeds', 2, 101, 'apple').do()
        self.assertEqual(WCAlg.fullrepr, '101.apple.seeds.WCAlg')
        self.assertEqual(WCAsp.fullrepr, '37.__all__.meditate.WCAsp')
        self.assertEqual(WCReg.fullrepr, '0.cherry.pit.WCReg')

def gather(*args, **kwds): return Aspect()
def retreat(*args, **kwds): return Timeline()
