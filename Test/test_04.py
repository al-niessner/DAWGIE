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
import dawgie.pl.scan
import os
import sys
import unittest

class Scan(unittest.TestCase):
    def __init__ (self, *args):
        unittest.TestCase.__init__(self, *args)
        self.__ae_dir = os.path.abspath (os.path.join
                                         (os.path.dirname (__file__), 'ae'))
        self.__ae_pkg = 'ae'
        sys.path.insert (0, os.path.abspath (os.path.dirname (__file__)))
        return

    def test (self):
        factories = dawgie.pl.scan.for_factories (self.__ae_dir, self.__ae_pkg)
        self.assertEqual (2, len (factories[dawgie.Factories.analysis]))
        self.assertEqual (1, len (factories[dawgie.Factories.events]))
        self.assertEqual (1, len (factories[dawgie.Factories.regress]))
        self.assertEqual (4, len (factories[dawgie.Factories.task]))
        for f in factories[dawgie.Factories.analysis]:\
            self.assertTrue (isinstance (f('a', 0, 0), dawgie.Analysis))
        for f in factories[dawgie.Factories.events]:
            for e in f(): self.assertTrue (isinstance (e, dawgie.EVENT))
        for f in factories[dawgie.Factories.regress]:\
            self.assertTrue (isinstance (f('r', 0, 0), dawgie.Regress))
        for f in factories[dawgie.Factories.task]:\
            self.assertTrue (isinstance (f('t', 0, 0, 0), dawgie.Task))
        return
    pass
