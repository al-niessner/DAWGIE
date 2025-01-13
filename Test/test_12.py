'''

COPYRIGHT:
Copyright (c) 2015-2025, California Institute of Technology ("Caltech").
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
import dawgie.db.test
import dawgie.pl.promotion
import unittest


class SVMock(dawgie.StateVector):
    def __init__(self, base):
        dawgie.StateVector.__init__(self)
        self.update(base)
        self._version_ = dawgie.VERSION(2, 2, 2)
        return

    pass


class VMock(dawgie.Value):
    def __init__(self):
        dawgie.Version.__init__(self)
        self._version_ = (3, 3, 3)
        return

    pass


class AlgMock(dawgie.Algorithm):
    def __init__(self):
        dawgie.Algorithm.__init__(self)
        self._version_ = (1, 1, 1)
        return

    def sv_as_dict(self):
        return {'d': SVMock({'e': VMock()}), 'g': SVMock({'h': VMock()})}

    pass


class NodeMock:
    def __init__(self, val: str, children: [] = []):
        self.__children = children
        self.__value = str
        return

    def __iter__(self):
        return self.__children.__iter__()

    @property
    def tag(self):
        return self.__value

    pass


class PromotionEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.allow_promotion = dawgie.context.allow_promotion
        cls.db_impl = dawgie.context.db_impl
        cls.promote = dawgie.pl.promotion.Engine()
        dawgie.context.allow_promotion = True
        dawgie.context.db_impl = 'test'
        return

    @classmethod
    def tearDownClass(cls):
        cls.promote = dawgie.pl.promotion.Engine()
        dawgie.context.allow_promotion = cls.allow_promotion
        dawgie.context.db_impl = cls.db_impl
        return

    def mock_consistent(
        self,
        inputs: [dawgie.db.REF],
        outputs: [dawgie.db.REF],
        target_name: str,
    ) -> ():
        if self.mock_behavior[0]:  # return a valid juncture
            return ((1, 2, 3, 4, 5), (6, 7, 8, 9, 0))
        return ()

    def mock_organize(self, task_names, runid=None, targets=None, event=None):
        self.assertListEqual(['b.f.g.h'], task_names)
        self.assertEqual(10101, runid)
        self.assertEqual(['a'], list(targets))

        if not self.mock_behavior[0]:
            self.assertEqual(
                'promotion not possible because no juncture found', event
            )
        elif not self.mock_behavior[1]:
            self.assertEqual('promotion failed to insert', event)
        else:
            self.assertEqual('path not possible', event)
        return

    def mock_promote(self, juncture: (), runid: int):
        self.assertTupleEqual(((1, 2, 3, 4, 5), (6, 7, 8, 9, 0)), juncture)
        return self.mock_behavior[1]

    def setUp(self):
        self.mock_behavior = [False, False]
        setattr(dawgie.db.test, 'consistent', self.mock_consistent)
        setattr(dawgie.db.test, 'promote', self.mock_promote)
        return

    def test_ae(self):
        ae = self.promote.ae
        self.promote.ae = None
        self.assertTrue(self.promote.ae is None)
        self.promote.ae = 1
        self.assertEqual(1, self.promote.ae)
        self.promote.ae = ae
        return

    def test_call(self):
        with self.assertLogs('dawgie.pl.promotion', level=0) as al:
            self.assertFalse(self.promote([('a.b.c', True)]))
            pass
        print(al.output)
        self.assertEqual(
            al.output,
            [
                'ERROR:dawgie.pl.promotion:Inconsistent arguments. Ignoring request.'
            ],
        )
        self.assertFalse(
            self.promote(
                [('a.b.c', True)], NodeMock('a.b', [NodeMock('c.d')]), 1
            )
        )
        self.assertTrue(
            self.promote(
                [('a.b.c', True), ('a.b.d', False)],
                NodeMock('a.b', [NodeMock('c.d')]),
                1,
            )
        )
        self.promote.clear()
        self.assertFalse(self.promote.more())
        return

    def test_do_allows(self):
        '''test allow to run conditions
        1. dawgie.context.allow_promotion is False
        2. No AE
        3. No organizer
        '''
        self.promote.clear()
        self.assertFalse(self.promote.more())
        self.promote.ae = None
        self.promote.organize = None
        with self.assertRaises(ValueError):
            self.promote.do()
        self.promote.ae = 1
        with self.assertRaises(ValueError):
            self.promote.do()
        ac = dawgie.context.allow_promotion
        dawgie.context.allow_promotion = False
        self.assertTrue(
            self.promote(
                [('a.b.c', True), ('a.b.d', False)],
                NodeMock('a.b', [NodeMock('c.d')]),
                1,
            )
        )
        self.assertFalse(self.promote.do())
        dawgie.context.allow_promotion = ac
        return

    def test_do(self):
        ct = 'b.c.d.e'
        root = dawgie.pl.dag.Node(
            'b.c', attrib={'do': [], 'doing': [], 'parents': [], 'todo': []}
        )
        node = dawgie.pl.dag.Node(
            'b.c.d.e',
            attrib={
                'alg': AlgMock(),
                'do': [],
                'doing': [],
                'parents': [],
                'todo': [],
            },
        )
        node = dawgie.pl.dag.Node(
            'b.f.g.h',
            attrib={
                'alg': AlgMock(),
                'do': [],
                'doing': [],
                'parents': [node],
                'todo': [],
            },
        )
        root.add(node)
        self.mock_behavior[0] = False
        self.mock_behavior[1] = False
        self.promote.organize = self.mock_organize
        self.promote.ae = {'b.f.g.h': [node]}
        self.assertTrue(dawgie.context.allow_promotion)
        self.promote.todo(root, 10101, [('1.a.' + ct, False)])
        self.assertTrue(self.promote.more())
        self.promote.do()
        self.mock_behavior[0] = True
        self.promote.do()
        self.mock_behavior[1] = True
        self.promote.do()
        return

    def test_more(self):
        self.promote.clear()
        self.assertFalse(self.promote.more())
        self.promote._todo['a'] = 1
        self.assertTrue(self.promote.more())
        self.promote.clear()
        self.assertFalse(self.promote.more())
        return

    def test_organize(self):
        organize = self.promote.organize
        self.promote.organize = None
        self.assertTrue(self.promote.organize is None)
        self.promote.organize = 1
        self.assertEqual(1, self.promote.organize)
        self.promote.organize = organize
        return

    def test_todo(self):
        self.promote.clear()
        self.assertFalse(self.promote.more())
        self.promote.todo(
            NodeMock('a.b', [NodeMock('c.d')]),
            1,
            values=[('a', True), ('b', True), ('c', True)],
        )
        self.assertFalse(self.promote.more())
        self.promote.clear()
        self.assertFalse(self.promote.more())
        self.promote.todo(
            NodeMock('a.b', [NodeMock('c.d')]),
            1,
            values=[('a', True), ('b', False), ('c', True)],
        )
        self.assertTrue(self.promote.more())
        self.promote.clear()
        self.assertFalse(self.promote.more())
        return

    pass
