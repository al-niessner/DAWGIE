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

import dawgie.context
import dawgie.pl.dag
import dawgie.pl.farm
import dawgie.pl.message
import unittest

class Farm(unittest.TestCase):
    @staticmethod
    def loseConnection(): return
    @staticmethod
    def write (b:bytes): return

    def test_hand__process(self):
        dawgie.context.git_rev = 321
        hand = dawgie.pl.farm.Hand(('localhost',666))
        hand.transport = self
        msg = dawgie.pl.message.make(rev=123,typ=dawgie.pl.message.Type.status)
        with self.assertLogs ('dawgie.pl.farm', 'WARN') as logbook:
            dawgie.pl.start.fsm.state = 'running'
            hand._process (msg)
            dawgie.pl.start.fsm.state = 'starting'
            pass
        self.assertEqual (['WARNING:dawgie.pl.farm:Worker and pipeline revisions are not the same. Sever version 123 and worker version 321.'], logbook.output)
        return

    def test_rerunid (self):
        n = dawgie.pl.dag.Node('a')
        r = dawgie.pl.farm.rerunid (n)
        self.assertEqual (2, r)
        n.set ('runid', 17)
        r = dawgie.pl.farm.rerunid (n)
        self.assertEqual (17, r)
        n.set ('runid', 0)
        r = dawgie.pl.farm.rerunid (n)
        self.assertEqual (0, r)
        return

    def test_something_to_do(self):
        self.assertFalse (dawgie.pl.farm.something_to_do())
        dawgie.pl.farm._agency = True
        self.assertFalse (dawgie.pl.farm.something_to_do())
        dawgie.pl.start.fsm.wait_on_crew.clear()
        self.assertFalse (dawgie.pl.farm.something_to_do())
        dawgie.pl.start.fsm.state = 'running'
        self.assertTrue (dawgie.pl.farm.something_to_do())
        dawgie.pl.start.fsm.state = 'starting'
        return
    pass
