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

from dawgie.pl.jobinfo import State

import datetime
import dawgie.context
import dawgie.pl.jobinfo
import dawgie.pl.schedule
import os
import sys
import unittest

class Schedule(unittest.TestCase):
    def __init__ (self, *args):
        unittest.TestCase.__init__(self, *args)
        self.__ae_dir = os.path.abspath (os.path.join
                                         (os.path.dirname (__file__), 'ae'))
        self.__ae_pkg = 'ae'
        sys.path.insert (0, os.path.abspath (os.path.dirname (__file__)))
        dawgie.context.db_impl = 'test'
        dawgie.context.git_rev = 'test'
        factories = dawgie.pl.scan.for_factories (self.__ae_dir, self.__ae_pkg)
        dawgie.pl.schedule.build (factories, [{},{},{}], [{},{},{},{}])
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

    def test__delay(self):
        import ae.network
        import ae.network.bot

        a = dawgie.schedule (ae.network.analysis,ae.network.bot.Analyzer(),True)
        b = dawgie.schedule (ae.network.task, ae.network.bot.Engine(), True)
        self.assertEqual (0, dawgie.pl.schedule._delay (a).total_seconds())
        self.assertEqual (0, dawgie.pl.schedule._delay (b).total_seconds())
        self.assertRaises (dawgie.pl.schedule._DelayNotKnowableError,
                           dawgie.pl.schedule._delay, a)
        return

    def test_complete(self):
        self.assertEqual (0, len (dawgie.pl.schedule.que))
        nodes = self._unravel (dawgie.pl.schedule.ae.at)
        dei = [node.tag for node in nodes].index ('disk.engine')
        for node in nodes:
            self.assertEqual (0, len(node.get('doing')) + len(node.get('todo')))
            pass
        nodes[dei].get ('doing').add ('b')
        dawgie.pl.schedule.que.append (nodes[dei])
        dawgie.pl.schedule.complete (nodes[dei], 3, 'b', {},
                                     dawgie.pl.jobinfo.State.success)
        self.assertEqual (0, len (dawgie.pl.schedule.que))
        nodes[dei].get ('doing').add ('d')
        nodes[dei].get ('todo').add ('f')
        dawgie.pl.schedule.que.append (nodes[dei])
        dawgie.pl.schedule.complete (nodes[dei], 3, 'd', {},
                                     dawgie.pl.jobinfo.State.success)
        self.assertEqual (1, len (dawgie.pl.schedule.que))
        nodes[dei].get ('doing').clear()
        nodes[dei].get ('todo').clear()
        dawgie.pl.schedule.que.clear()
        return

    def test_defer(self):
        dawgie.pl.schedule.periodics ([fake_events_defer])
        dawgie.pl.schedule.defer()
        self.assertEqual (3, len (dawgie.pl.schedule.per))
        for p in dawgie.pl.schedule.per:
            if p.tag == 'disk.engine':
                self.assertEqual (State.waiting, p.get ('status'))
            elif p.tag == 'network.analyzer':
                self.assertEqual (State.delayed, p.get ('status'))
            else: self.assertTrue (False, 'unxpected element ' + p.tag)
            pass
        self.assertEqual (2, len (dawgie.pl.schedule.que))
        for e in dawgie.pl.schedule.que:
            self.assertEqual (State.waiting, e.get ('status'))
            pass
        dawgie.pl.schedule.per.clear()
        dawgie.pl.schedule.que.clear()
        return

    def test_next(self):
        self.assertEqual (0, len (dawgie.pl.schedule.que))
        nodes = self._unravel (dawgie.pl.schedule.ae.at)
        dei = [node.tag for node in nodes].index ('disk.engine')
        na = [node.tag for node in nodes].index ('network.analyzer')
        noio = [node.tag for node in nodes].index ('noio.engine')
        for node in nodes:
            self.assertEqual (0, len(node.get('doing')) + len(node.get('todo')))
            pass
        nodes[noio].get ('todo').update (['a', 'c', 'd'])
        dawgie.pl.schedule.que.append (nodes[noio])
        dispatch = dawgie.pl.schedule.next_job_batch()
        self.assertEqual (1, len (dispatch))
        self.assertEqual ('noio.engine', dispatch[0].tag)
        self.assertEqual (0, len (nodes[noio].get ('todo')))
        self.assertEqual (3, len (nodes[noio].get ('do')))
        self.assertEqual (3, len (nodes[noio].get ('doing')))
        nodes[noio].get ('do').clear()
        nodes[noio].get ('doing').clear()
        dawgie.pl.schedule.que.append (nodes[na])
        nodes[na].get ('todo').update (['__all__'])
        nodes[noio].get ('todo').update (['a', 'c', 'd'])
        dispatch = dawgie.pl.schedule.next_job_batch()
        self.assertEqual (1, len (dispatch))
        self.assertEqual ('network.analyzer', dispatch[0].tag)
        self.assertEqual (0, len (nodes[na].get ('todo')))
        self.assertEqual (1, len (nodes[na].get ('do')))
        self.assertEqual (1, len (nodes[na].get ('doing')))
        self.assertEqual (3, len (nodes[noio].get ('todo')))
        self.assertEqual (0, len (nodes[noio].get ('do')))
        self.assertEqual (0, len (nodes[noio].get ('doing')))
        nodes[na].get ('do').clear()
        nodes[na].get ('doing').clear()
        dawgie.pl.schedule.que.remove (nodes[na])
        dawgie.pl.schedule.que.append (nodes[dei])
        nodes[dei].get ('todo').update (['a', 'd', 'e', 'f', 'g'])
        dispatch = dawgie.pl.schedule.next_job_batch()
        self.assertEqual (2, len (dispatch))
        self.assertEqual ('disk.engine', dispatch[0].tag)
        self.assertEqual ('noio.engine', dispatch[1].tag)
        self.assertEqual (0, len (nodes[dei].get ('todo')))
        self.assertEqual (5, len (nodes[dei].get ('do')))
        self.assertEqual (5, len (nodes[dei].get ('doing')))
        self.assertEqual (2, len (nodes[noio].get ('todo')))
        self.assertEqual (1, len (nodes[noio].get ('do')))
        self.assertEqual (1, len (nodes[noio].get ('doing')))
        dawgie.pl.schedule.que.clear()
        for idx in [dei, na, noio]:
            for attr in ['do', 'doing', 'todo']: nodes[idx].get (attr).clear()
            pass
        return

    def test_organize(self):
        self.assertEqual (0, len (dawgie.pl.schedule.que))
        nodes = self._unravel (dawgie.pl.schedule.ae.at)
        for node in nodes:
            self.assertEqual (0, len(node.get('doing')) + len(node.get('todo')))
            pass
        dawgie.pl.schedule.organize (['disk.engine'], 3, ['c','e','g'])
        for node in nodes:
            if node.tag == 'disk.engine':
                self.assertEqual (0, len (node.get ('doing')))
                self.assertEqual (3, len (node.get ('todo')))
                node.get ('todo').clear()
            else: self.assertEqual (0, (len(node.get('doing')) +
                                        len(node.get('todo'))))
            pass
        self.assertEqual (1, len (dawgie.pl.schedule.que))
        dawgie.pl.schedule.que.clear()
        return

    def test_tasks(self):
        tasks = dawgie.pl.schedule.tasks()
        self.assertEqual (12, len (tasks))
        return

    def test_update(self):
        root = [n for n in filter (lambda n:n.tag.startswith ('network.'),
                                   dawgie.pl.schedule.ae.at)][0]
        root.get ('doing').add ('fred')
        for c in root:
            if c.tag == 'disk.engine': c.get ('doing').add ('fred')
            pass
        dawgie.pl.schedule.que.clear()
        dawgie.pl.schedule.update (['12.fred.network.analyzer.test.image'],
                                   root, 12)
        self.assertEqual (len (root), len (dawgie.pl.schedule.que))
        for n in dawgie.pl.schedule.que:\
            self.assertEqual (12, n.get ('runid'), n.tag)
        return

    def test_view_events(self):
        dawgie.pl.schedule.periodics ([fake_events_view])
        events = dawgie.pl.schedule.view_events()
        events = dict ([(e['actor'],e['delays']) for e in events])
        self.assertEqual (2, len(events))
        self.assertTrue ('disk.engine' in events)
        self.assertEqual (2, len (events['disk.engine']))
        self.assertAlmostEqual (86400, events['disk.engine'][0], -1)
        self.assertAlmostEqual (518400, events['disk.engine'][1], -1)
        self.assertTrue ('network.analyzer' in events)
        self.assertEqual (1, len (events['network.analyzer']))
        self.assertEqual (0, events['network.analyzer'][0])
        dawgie.pl.schedule.per.clear()
        return
    pass

def fake_events_defer():
    import ae.disk
    import ae.disk.bot
    import ae.network
    import ae.network.bot
    now = datetime.datetime.utcnow()
    return [dawgie.schedule(ae.disk.task, ae.disk.bot.Engine(),
                            dow=now.weekday(), time=now.time()),
            dawgie.schedule(ae.network.analysis, ae.network.bot.Analyzer(),
                            dow=(now.weekday() + 1) % 7, time=now.time())]

def fake_events_view():
    import ae.disk
    import ae.disk.bot
    import ae.network
    import ae.network.bot
    now = datetime.datetime.utcnow()
    return [dawgie.schedule(ae.disk.task, ae.disk.bot.Engine(),
                            dow=(now.weekday()+1) % 7, time=now.time()),
            dawgie.schedule(ae.disk.task, ae.disk.bot.Engine(),
                            dow=(now.weekday()-1) % 7, time=now.time()),
            dawgie.schedule(ae.network.analysis, ae.network.bot.Analyzer(),
                            boot=True)]
