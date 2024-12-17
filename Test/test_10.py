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

import mock

import dawgie.context
import dawgie.pl.dag
import dawgie.pl.farm
import dawgie.pl.message
import dawgie.pl.schedule
import os
import shutil
import tempfile
import unittest


class Farm(unittest.TestCase):
    @staticmethod
    def loseConnection():
        return

    @staticmethod
    def write(b: bytes):
        return

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()
        os.mkdir(os.path.join(cls.root, 'db'))
        os.mkdir(os.path.join(cls.root, 'dbs'))
        os.mkdir(os.path.join(cls.root, 'logs'))
        os.mkdir(os.path.join(cls.root, 'stg'))
        dawgie.context.db_impl = 'shelve'
        dawgie.context.db_name = 'testspace'
        dawgie.context.db_path = os.path.join(cls.root, 'db')
        dawgie.context.data_dbs = os.path.join(cls.root, 'dbs')
        dawgie.context.data_log = os.path.join(cls.root, 'logs')
        dawgie.context.data_stg = os.path.join(cls.root, 'stg')
        return

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, True)
        return

    def test_hand__process(self):
        dawgie.context.git_rev = 321
        hand = dawgie.pl.farm.Hand(('localhost', 666))
        hand.transport = self
        msg = dawgie.pl.message.make(rev=123, typ=dawgie.pl.message.Type.status)
        with self.assertLogs('dawgie.pl.farm', 'WARN') as logbook:
            dawgie.context.fsm.state = 'running'
            hand._process(msg)
            dawgie.context.fsm.state = 'starting'
            pass
        self.assertEqual(
            [
                'WARNING:dawgie.pl.farm:Worker and pipeline revisions are not the same. Sever version 123 and worker version 321.'
            ],
            logbook.output,
        )
        return

    def test_hand__res(self):
        a = dawgie.pl.dag.Node('a')
        b = dawgie.pl.dag.Node('b')
        c = dawgie.pl.dag.Node('c')
        d = dawgie.pl.dag.Node('d')
        e = dawgie.pl.dag.Node('e')
        f = dawgie.pl.dag.Node('f')
        for n in [a, b, c, d, e, f]:
            for l in ['do', 'doing', 'todo']:
                n.set(l, [])
                for t in ['A', 'B', 'C']:
                    n.get(l).append(t)
                pass
            pass
        a.add(c)
        a.add(d)
        b.add(d)
        b.add(e)
        d.add(f)
        dawgie.pl.schedule.que.extend([a, b, c, d, e, f])
        dawgie.pl.farm.Hand._res(
            dawgie.pl.message.make(
                inc='B', jid='b', rid=42, suc=None, tim={}, val=[]
            )
        )
        for l in ['do', 'doing', 'todo']:
            self.assertEqual(['A', 'B', 'C'], a.get(l))
            self.assertEqual(['A', 'C'], b.get(l))
            self.assertEqual(['A', 'B', 'C'], c.get(l))
            self.assertEqual(['A', 'C'], d.get(l))
            self.assertEqual(['A', 'C'], e.get(l))
            self.assertEqual(['A', 'C'], f.get(l))
            pass
        return

    def test_rerunid(self):
        dawgie.db.open()
        n = dawgie.pl.dag.Node('a')
        r = dawgie.pl.farm.rerunid(n)
        self.assertGreater(r, 0)
        n.set('runid', 17)
        r = dawgie.pl.farm.rerunid(n)
        self.assertEqual(17, r)
        n.set('runid', 0)
        r = dawgie.pl.farm.rerunid(n)
        self.assertEqual(0, r)
        dawgie.db.close()
        return

    def test_something_to_do(self):
        self.assertFalse(dawgie.pl.farm.something_to_do())
        dawgie.pl.farm._agency = True
        self.assertFalse(dawgie.pl.farm.something_to_do())
        dawgie.context.fsm.wait_on_crew.clear()
        self.assertFalse(dawgie.pl.farm.something_to_do())
        dawgie.context.fsm.state = 'running'
        self.assertTrue(dawgie.pl.farm.something_to_do())
        dawgie.context.fsm.state = 'starting'
        return

    pass
