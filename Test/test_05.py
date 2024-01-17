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

import dawgie.pl.dag
import dawgie.pl.scan
import os
import sys
import unittest

class DAG(unittest.TestCase):
    def __init__ (self, *args):
        unittest.TestCase.__init__(self, *args)
        self.__ae_dir = os.path.abspath (os.path.join
                                         (os.path.dirname (__file__), 'ae'))
        self.__ae_pkg = 'ae'
        sys.path.insert (0, os.path.abspath (os.path.dirname (__file__)))
        factories = dawgie.pl.scan.for_factories (self.__ae_dir, self.__ae_pkg)
        self.__dag = dawgie.pl.dag.Construct(factories)
        return

    def _unravel (self, nodes)->[]:
        result = set()
        for node in nodes:
            children = []
            for child in node:
                if (dawgie.pl.dag.Construct.trim (child.tag, 2) !=
                    dawgie.pl.dag.Construct.trim (node.tag, 2)):\
                   children.append (child)
                pass
            result.add (node)
            result.update (self._unravel (children))
            pass
        return list (result)

    def test_tree(self):
        self.assertEqual (3, len (self.__dag.at))
        root = list(self.__dag.at)
        root = [r for r in filter(lambda n:n.tag.startswith('network'),root)][0]
        self.assertEqual ('network.analyzer', root.tag)
        self.assertEqual (4, len (root))
        children = list(root)
        self.assertTrue ('network.engine' in [child.tag for child in children])
        self.assertTrue ('disk.engine' in [child.tag for child in children])
        grands = set()
        for child in children:
            if child.tag.startswith ('review.'): self.assertEqual(0,len(child))
            else:
                self.assertEqual (1, len(child))
                grands.update (list (child))
                pass
            pass
        self.assertEqual (2, len (grands))
        print ([n.tag for n in grands])
        self.assertTrue ('disk.engine' in [node.tag for node in grands])
        self.assertTrue ('noio.engine' in [node.tag for node in grands])

        root = list(self.__dag.at)
        root = [r for r in
                filter (lambda n:n.tag.startswith ('feedback.co'), root)][0]
        self.assertEqual ('feedback.command', root.tag)
        self.assertEqual (1, len (root))
        self.assertEqual ('feedback.sum', root[0].tag)
        children = list(root[0])
        self.assertEqual (1, len (children))
        self.assertEqual ('feedback.control', children[0].tag)
        children = list(children[0])
        self.assertEqual (2, len (children))
        self.assertTrue ('feedback.control' in [child.tag for child in children])
        self.assertTrue ('feedback.model' in [child.tag for child in children])
        return

    def test_parents(self):
        nodes = self._unravel (self.__dag.vt)
        parents = {'disk.engine.test.image':['network.analyzer.test.image',
                                             'network.engine.test.image'],
                     'feedback.command.request.voltage':[],
                     'feedback.control.law.P':['feedback.sum.total.voltage'],
                     'feedback.control.law.I':['feedback.sum.total.voltage'],
                     'feedback.control.law.D':['feedback.sum.total.voltage'],
                     'feedback.control.response.accum':['feedback.sum.total.voltage'],
                     'feedback.control.response.voltage':['feedback.sum.total.voltage'],
                     'feedback.sensor.measured.voltage':[],
                     'feedback.sum.total.voltage':['feedback.command.request.voltage', 'feedback.sensor.measured.voltage'],
                     'feedback.model.voltage.value':['feedback.control.response.voltage'],
                     'feedback.output.actual.voltage':['feedback.model.voltage.value'],
                   'network.analyzer.test.image':[],
                   'network.engine.test.image':['network.analyzer.test.image'],
                   'noio.engine.test.image':['disk.engine.test.image'],
                   'review.aspect.test.image':['network.analyzer.test.image'],
                   'review.history.test.image':['network.analyzer.test.image']}
        self.assertEqual (16, len (nodes))
        for node in nodes:
            print (node.tag)
            self.assertTrue (node.tag in parents)
            print (node.tag, sorted ([p.tag for p in node.get ('parents')]))
            self.assertEqual (parents[node.tag],
                              sorted ([p.tag for p in node.get ('parents')]))
            pass
        return

    def test_ancestry(self):
        nodes = self._unravel (self.__dag.vt)
        ancestors = {'disk.engine.test.image':['network.analyzer.test.image',
                                               'network.engine.test.image'],
                     'feedback.command.request.voltage':[],
                     'feedback.control.law.P':['feedback.command.request.voltage', 'feedback.sensor.measured.voltage', 'feedback.sum.total.voltage'],
                     'feedback.control.law.I':['feedback.command.request.voltage', 'feedback.sensor.measured.voltage', 'feedback.sum.total.voltage'],
                     'feedback.control.law.D':['feedback.command.request.voltage', 'feedback.sensor.measured.voltage', 'feedback.sum.total.voltage'],
                     'feedback.control.response.accum':['feedback.command.request.voltage', 'feedback.sensor.measured.voltage', 'feedback.sum.total.voltage'],
                     'feedback.control.response.voltage':['feedback.command.request.voltage', 'feedback.sensor.measured.voltage', 'feedback.sum.total.voltage'],
                     'feedback.sensor.measured.voltage':[],
                     'feedback.sum.total.voltage':['feedback.command.request.voltage', 'feedback.sensor.measured.voltage'],
                     'feedback.model.voltage.value':['feedback.command.request.voltage', 'feedback.control.response.voltage', 'feedback.sensor.measured.voltage', 'feedback.sum.total.voltage'],
                     'feedback.output.actual.voltage':['feedback.command.request.voltage', 'feedback.control.response.voltage', 'feedback.model.voltage.value', 'feedback.sensor.measured.voltage', 'feedback.sum.total.voltage'],
                     'network.analyzer.test.image':[],
                     'network.engine.test.image':['network.analyzer.test.image'],
                     'noio.engine.test.image':['disk.engine.test.image',
                                               'network.analyzer.test.image',
                                               'network.engine.test.image'],
                     'review.aspect.test.image':['network.analyzer.test.image'],
                     'review.history.test.image':['network.analyzer.test.image']}
        self.assertEqual (16, len (nodes))
        for node in nodes:
            self.assertTrue (node.tag in ancestors)
            print (node.tag, sorted ([a for a in node.get ('ancestry')]))
            self.assertEqual (ancestors[node.tag],
                              sorted ([a for a in node.get ('ancestry')]))
        return
    pass
