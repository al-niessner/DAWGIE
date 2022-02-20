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
import dawgie
import numpy
import os
import pickle
import tempfile
import unittest

class Metric(unittest.TestCase):
    @staticmethod
    def _cpu (N):
        for n in range(N):
            x = numpy.random.rand (1000,1000)
            y = numpy.random.rand (1000,1000)
            z = x * y
            pass
        return

    @staticmethod
    def _io (N):
        fid,fn = tempfile.mkstemp()
        os.close (fid)
        for n in range(N):
            x = numpy.random.rand (1200,1200)
            with open (fn, 'bw') as f: pickle.dump (x, f)
            with open (fn, 'br') as f: y = pickle.load (f)
            pass
        os.unlink (fn)
        return

    def test_cpu(self):
        m = dawgie._Metric()
        m.measure (Metric._cpu, (100,))
        s = m.sum()
        self.assertTrue (30000 < s.mem)
        self.assertTrue (1.0 < s.user)
        return

    def test_io(self):
        m = dawgie._Metric()
        m.measure (Metric._io, (100,))
        s = m.sum()
        print ('metric:', s)
        # self.assertTrue (1400000 < s.input)
        self.assertLess (1400000, s.output)
        self.assertLess (3000, s.mem)
        self.assertLess (0.0, s.sys)
        self.assertLess (0.0, s.user)
        return
    pass
