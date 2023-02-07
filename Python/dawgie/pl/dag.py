'''
COPYRIGHT:
Copyright (c) 2015-2023, California Institute of Technology ("Caltech").
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

from dawgie.pl.jobinfo import State

import dawgie
import dawgie.context
import dawgie.util
import enum
import logging; log = logging.getLogger (__name__)
import os
import pydot
import xml.etree.ElementTree

class Construct:
    # pylint: disable=too-many-instance-attributes
    def __getitem__(self, key):
        result = []

        if key.count ('.') == 3: result.append (self._flat[key])
        else:
            key = key + '.'
            for k,v in self._flat.items():
                if k.startswith (key): result.append (v)
                pass
            pass
        return result

    def __init__(self, factories):
        self._flat = {}
        self._roots = set()
        log.info ('Construct() - build aspect tree')
        self._build_tree (factories[dawgie.Factories.analysis], Shape.rectangle,
                          self._sub_analysis, 'traits')
        log.info ('Construct() - build regression tree')
        self._build_tree (factories[dawgie.Factories.regress], Shape.octagon,
                          self._sub_regression, 'variables')
        log.info ('Construct() - build task tree')
        self._build_tree (factories[dawgie.Factories.task], Shape.ellipse,
                          self._sub_task, 'previous')
        self._feedbacks = {}
        self._feedback()
        log.info ('Construct() - build parents')
        self._parents (self._roots, set())
        log.info ('Construct() - build ancestry')
        self._ancestry()
        log.info ('Construct() - trim tree to algorithms')
        self._at = self._trim_trees (2)
        log.info ('Construct() - trim tree to state vectors')
        self._svt = self._trim_trees (3)
        log.info ('Construct() - trim tree to tasks')
        self._tt = self._trim_trees (1)
        self._vt = self._roots
        log.info ('Construct() - graph algorithm tree')
        self._av = self.graph (pydot.Dot(graph_type='digraph', rank='same'),
                               self._at, 'av.svg')
        log.info ('Construct() - graph state vector tree')
        self._svv = self.graph (pydot.Dot(graph_type='digraph', rank='same'),
                                self._svt, 'svt.png')
        log.info ('Construct() - graph task tree')
        self._tv = self.graph (pydot.Dot(graph_type='digraph', rank='same'),
                               self._tt, 'tv.svg')
        log.info ('Construct() - graph value tree')
        self._vv = self.graph (pydot.Dot(graph_type='digraph', rank='same'),
                               self._vt, 'vv.svg')
        return

    def _ancestry (self):
        for name,dct in self._flat.items():
            heritage = dct.get ('parents').copy()
            parents = heritage.copy()
            while parents:
                grands = set()
                for p in filter (lambda p,n=name: p.tag != n, parents):
                    heritage.update (self._flat[p.tag].get ('parents'))
                    grands.update (self._flat[p.tag].get ('parents'))
                    pass
                parents = grands
                pass
            dct.get ('ancestry').update ([h.tag for h in heritage])
            pass
        return

    def _build_tree (self, factories, shape, sub_algs, sub_dep):
        for factory in factories:
            bot = factory (dawgie.util.task_name (factory), -1)
            for alg in bot.list():
                for sv in alg.state_vectors():
                    for vn in sv:
                        fn = '.'.join ([bot._name(), alg.name(), sv.name(), vn])

                        if fn not in self._flat:\
                           self._flat[fn] = Node(fn,
                                                 attrib={'alg':alg,
                                                         'ancestry':set(),
                                                         'factory':factory,
                                                         'feedback':set(),
                                                         'parents':set()})
                        else: self._flat[fn].set ('factory', factory)

                        if not getattr(alg,sub_dep)():\
                           self._roots.add (self._flat[fn])

                        self._flat[fn].set ('shape', shape)
                        sub_algs (alg, fn)
                        pass
                    pass
                pass
            pass
        return

    def _feedback(self):
        for node in self._flat.values():
            for vref in dawgie.util.as_vref (node.get ('alg').feedback()):
                fbn = dawgie.util.vref_as_name (vref)
                node.get ('feedback').add (self._flat[fbn])
                self._feedbacks[fbn] = node.tag
                pass
            pass
        return

    def _parents (self, nodes:'[Node]', known):
        for node in nodes:
            children = []
            known.add (node.tag)
            for child in node:
                if self.trim (child.tag, 2) != self.trim (node.tag, 2):\
                   children.append (child)
                pass
            for child in children: child.get ('parents').add (node)
            children = list(filter (lambda n,k=known:n.tag not in k, children))
            self._parents (list(filter (lambda n,k=known:n.tag not in k,
                                        children)), known)
            pass
        return

    def _sub_analysis (self, a, fn):
        for ref in dawgie.util.as_vref (a.traits()):
            pf,pi = ref.factory,ref.impl
            pn = '.'.join ([dawgie.util.task_name (pf), pi.name(),
                            ref.item.name(), ref.feat])

            if pn not in self._flat:\
               self._flat[pn] = Node(pn, attrib={'alg':pi,
                                                 'ancestry':set(),
                                                 'factory':pf,
                                                 'feedback':set(),
                                                 'parents':set()})
            self._flat[pn].add (self._flat[fn])
            pass
        return

    def _sub_regression (self, a, fn):
        for ref in dawgie.util.as_vref (a.variables()):
            pf,pi, = ref.factory, ref.impl
            pn = '.'.join ([dawgie.util.task_name (pf), pi.name(),
                            ref.item.name(), ref.feat])

            if pn not in self._flat:\
               self._flat[pn] = Node(pn, attrib={'alg':pi,
                                                 'ancestry':set(),
                                                 'factory':pf,
                                                 'feedback':set(),
                                                 'parents':set()})
            self._flat[pn].add (self._flat[fn])
            pass
        return

    def _sub_task (self, a, fn):
        for ref in dawgie.util.as_vref (a.previous()):
            pf,pi, = ref.factory, ref.impl
            pn = '.'.join ([dawgie.util.task_name (pf), pi.name(),
                            ref.item.name(), ref.feat])

            if pn not in self._flat:\
               self._flat[pn] = Node(pn, attrib={'alg':pi,
                                                 'ancestry':set(),
                                                 'factory':pf,
                                                 'feedback':set(),
                                                 'parents':set()})
            self._flat[pn].add (self._flat[fn])
            pass
        return

    def _trim_trees (self, length):
        result = []
        trimmed = {Construct.trim (leaf, length) for leaf in self._flat}
        trimmed = {name:Node(name, attrib={'feedback':set(),
                                           'shape':Shape.component,
                                           'visitors':set()})
                        for name in trimmed}
        for root in self._roots: result.append (root.trim (trimmed, length))
        return result

    @property
    def at(self)->'[Node]': return self._at
    @property
    def av(self): return self._av
    @property
    def svt(self)->'[Node]': return self._svt
    @property
    def svv(self): return self._svv
    @property
    def tt(self)->'[Node]': return self._tt
    @property
    def tv(self): return self._tv
    @property
    def vt(self)->'[Node]': return self._vt
    @property
    def vv(self): return self._vv

    @property
    def feedbacks(self)->{str:str}: return self._feedbacks

    @staticmethod
    def graph (dot:pydot.Dot, roots:set, name:str):
        for root in roots: root.graph (dot)
        idir = os.path.abspath (os.path.join (dawgie.context.fe_path,
                                              'images/svg'))

        if not os.path.isdir (idir): os.makedirs (idir)

        fn = os.path.join (idir, name)
        dot.write_svg (fn)
        with open (fn, 'rb') as f: data = f.read()
        return data

    @staticmethod
    def trim (tag, length): return '.'.join (tag.split('.')[:length])

    pass

class Node(xml.etree.ElementTree.Element):
    # pylint: disable=dangerous-default-value,protected-access
    def __hash__ (self):
        return self.tag.__hash__()

    def __pydotify (self):
        ready = all ((self.tag.find (c) < 0 for c in ['.', '(', ')']))
        return self.tag if ready else (f'"{self.tag}"')

    def __pydotnode (self, dot):
        name = self.__pydotify()
        if not dot.get_node (name):
            shape = self.get ('shape')
            shape = shape.name if shape else 'diamond'
            dot.add_node (pydot.Node(name,
                                     id=name.replace ('.', '_'),
                                     shape=shape))
            pass
        return dot.get_node (name)[0]

    def _reset (self):
        if self.get ('been_here', True):
            self.set ('been_here', False)
            for c in self: c._reset()
            pass
        pass

    def add (self, item):
        names = [c.tag for c in self]
        if item.tag not in names: self.append (item)
        return

    def graph (self, dot, level=0, cycle=False):
        if cycle or not self.get ('been_here', False):
            self.set ('been_here', True)
            cl = self.get ('level')
            self.set ('level', max (level, 0 if cl is None else cl))
            src = self.__pydotnode (dot)
            for c in self:
                dst = c.__pydotnode (dot)
                if not dot.get_edge (self.__pydotify(), c.__pydotify()):
                    dot.add_edge (pydot.Edge(src, dst))
                    pass
                c.graph (dot, level + 1, cycle)
                pass
            for f in self.get ('feedback'):
                dst = f.__pydotnode (dot)
                if not dot.get_edge (f.__pydotify(), self.__pydotify()):
                    dot.add_edge (pydot.Edge(dst, src, style='dashed'))
                    pass
                pass
            pass
        return

    def iter(self, tag=None):
        """Create tree iterator.

        The iterator loops over the element and all subelements in document
        order, returning all elements with a matching tag.

        If the tree structure is modified during iteration, new or removed
        elements may or may not be included.  To get a stable set, use the
        list() function on the iterator, and loop over the resulting list.

        *tag* is what tags to look for (default is to return all elements)

        Return an iterator containing all the matching elements.

        """
        if tag == "*": tag = None
        if tag is None or self.tag == tag: yield self
        for e in filter (lambda c,me=self.tag:c.tag != me, self):
            yield from e.iter(tag)
            pass
        return

    def locate (self, name):
        result = [self] if name == self.tag else []
        for child in filter (lambda c,n=self.tag: c.tag != n, self):
            result.extend (child.locate (name))
        return result

    def trim (self, known, length):
        short_name = Construct.trim (self.tag, length)
        short_node = known[short_name]

        if 1 < length: short_node.set ('shape', self.get ('shape'))
        if length == 2 and not short_node.get ('alg'):
            short_node.set ('alg', self.get ('alg'))
            short_node.set ('do', set())
            short_node.set ('doing', set())
            short_node.set ('factory', self.get ('factory'))
            short_node.set ('status', State.initial)
            short_node.set ('todo', set())
            pass
        if length == 2:
            aset = short_node.get ('ancestry')
            aset = aset if aset else set()
            aset.update ([Construct.trim (a, length) for a in self.get ('ancestry')])
            short_node.set ('ancestry', aset)
            pass
        if self.tag not in short_node.get ('visitors'):
            short_node.get ('visitors').add (self.tag)
            for f in self.get ('feedback'):\
                short_node.get ('feedback').add (f.trim (known, length))
            for c in self: short_node.add (c.trim (known, length))
            pass
        return short_node
    pass

@enum.unique
class Shape(enum.Enum):
    component = 4
    ellipse = 0
    hexagon = 2
    invhouse = 5
    octagon = 3
    rectangle = 1
    pass
