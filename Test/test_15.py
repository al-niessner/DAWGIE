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

import dawgie
import dawgie.db
import dawgie.pl.schedule
import dawgie.util
import dawgie.util.names
import unittest


class Analysis(dawgie.Analysis):
    def __init__(self, name, ps_hint, runid, al):
        dawgie.Analysis.__init__(self, name, ps_hint, runid)
        self._al = al
        pass

    def list(self):
        return self._al

    pass


class Regress(dawgie.Regress):
    def __init__(self, name, ps_hint, target, rl):
        dawgie.Regress.__init__(self, name, ps_hint, target)
        self._rl = rl
        pass

    def list(self):
        return self._rl

    pass


class StateVector(dawgie.StateVector):
    def name(self):
        return 'sv'

    def view(self, visitor):
        pass

    pass


class Task(dawgie.Task):
    def __init__(self, name, ps_hint, runid, target, tl):
        dawgie.Task.__init__(self, name, ps_hint, runid, target)
        self._tl = tl
        pass

    def list(self):
        return self._tl

    pass


class Work(dawgie.Algorithm, dawgie.Analyzer, dawgie.Regression):
    def __init__(self, fb: [], name: str, prev: []):
        dawgie.Algorithm.__init__(self)
        dawgie.Analyzer.__init__(self)
        dawgie.Regression.__init__(self)
        self._fb = fb
        self._name = name
        self._prev = prev
        self._sv = StateVector()
        self._sv['goat'] = dawgie.Value()
        pass

    def feedback(self):
        return self._fb

    def name(self):
        return self._name

    def previous(self):
        return self._prev

    def run(self, *args, **kwds):
        pass

    def state_vectors(self):
        return [self._sv]

    def traits(self):
        return self._prev

    def variables(self):
        return self._prev

    pass


class ScheduleRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._targets_orig = getattr(dawgie.db, 'targets')
        cls._task_name_orig = getattr(dawgie.util.names, 'task_name')
        setattr(dawgie.db, 'targets', _mock_targets)
        setattr(dawgie.util, 'task_name', _mock_task_name)
        setattr(dawgie.util.names, 'task_name', _mock_task_name)
        factories = {
            dawgie.Factories.analysis: [analysis],
            dawgie.Factories.events: [events],
            dawgie.Factories.regress: [regress],
            dawgie.Factories.task: [task],
        }
        dawgie.pl.schedule.build(factories, [{}, {}, {}], [{}, {}, {}, {}])
        # use the print output to observe what the DAG for this test look like
        print('av:', dawgie.pl.schedule.ae.av.decode())
        return

    @classmethod
    def tearDownClass(cls):
        setattr(dawgie.db, 'targets', cls._targets_orig)
        setattr(dawgie.util, 'task_name', cls._task_name_orig)
        setattr(dawgie.util.names, 'task_name', cls._task_name_orig)
        return

    def test_issue_194(self):
        dawgie.pl.schedule.organize(
            ['test_15.root'], event='test for issue 194', targets=['__all__']
        )
        self.assertEqual(
            dawgie.pl.schedule.view_todo(),
            [
                {
                    'name': 'test_15.root',
                    'targets': [
                        'Target_0',
                        'Target_1',
                        'Target_2',
                        'Target_3',
                        'Target_4',
                        'Target_5',
                        'Target_6',
                        'Target_7',
                        'Target_8',
                        'Target_9',
                    ],
                }
            ],
        )
        jobs = dawgie.pl.schedule.next_job_batch()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(
            jobs[0].get('status'), dawgie.pl.schedule.State.waiting
        )
        jobs[0].set('status', dawgie.pl.schedule.State.running)
        jobs[0].get('do').clear()
        dawgie.pl.schedule.complete(
            jobs[0], 1, 'Target_3', {}, dawgie.pl.schedule.State.success
        )
        self.assertNotIn('Target_3', jobs[0].get('doing'))
        dawgie.pl.schedule.update(
            [('1.Target_3.test_15.root.sv.goat', True)], jobs[0], 1
        )
        jobs.extend(dawgie.pl.schedule.next_job_batch())
        self.assertEqual(len(jobs), 3)
        jobs[1].set('status', dawgie.pl.schedule.State.running)
        jobs[1].get('do').clear()
        dawgie.pl.schedule.complete(
            jobs[1], 1, 'Target_3', {}, dawgie.pl.schedule.State.success
        )
        self.assertNotIn('Target_3', jobs[1].get('doing'))
        self.assertEqual(0, len(jobs[1].get('doing')))
        dawgie.pl.schedule.update(
            [('1.Target_3.test_15.A.sv.goat', True)], jobs[1], 1
        )
        jobs[2].set('status', dawgie.pl.schedule.State.running)
        jobs[2].get('do').clear()
        dawgie.pl.schedule.complete(
            jobs[2], 1, 'Target_3', {}, dawgie.pl.schedule.State.success
        )
        self.assertNotIn('Target_3', jobs[2].get('doing'))
        self.assertEqual(0, len(jobs[1].get('doing')))
        dawgie.pl.schedule.update(
            [('1.Target_3.test_15.B.sv.goat', True)], jobs[2], 1
        )
        _clean(jobs)
        self.assertEqual(len(jobs), 1)
        jobs.extend(dawgie.pl.schedule.next_job_batch())
        self.assertEqual(len(jobs), 2)
        jobs[1].set('status', dawgie.pl.schedule.State.running)
        jobs[1].get('do').clear()
        dawgie.pl.schedule.complete(
            jobs[1], 1, 'Target_3', {}, dawgie.pl.schedule.State.success
        )
        self.assertNotIn('Target_3', jobs[1].get('doing'))
        self.assertEqual(0, len(jobs[1].get('doing')))
        dawgie.pl.schedule.update(
            [('1.Target_3.test_15.C.sv.goat', True)], jobs[1], 1
        )
        _clean(jobs)
        self.assertEqual(len(jobs), 1)
        jobs.extend(dawgie.pl.schedule.next_job_batch())
        self.assertEqual(len(jobs), 2)
        jobs[1].set('status', dawgie.pl.schedule.State.running)
        jobs[1].get('do').clear()
        dawgie.pl.schedule.complete(
            jobs[1], 1, 'Target_3', {}, dawgie.pl.schedule.State.success
        )
        self.assertNotIn('Target_3', jobs[1].get('doing'))
        self.assertEqual(0, len(jobs[1].get('doing')))
        dawgie.pl.schedule.update(
            [('1.Target_3.test_15.A.sv.goat', False)], jobs[1], 1
        )
        _clean(jobs)
        self.assertEqual(len(jobs), 1)
        jobs.extend(dawgie.pl.schedule.next_job_batch())
        self.assertEqual(len(jobs), 2)
        jobs[1].set('status', dawgie.pl.schedule.State.running)
        jobs[1].get('do').clear()
        dawgie.pl.schedule.complete(
            jobs[1], 1, 'Target_3', {}, dawgie.pl.schedule.State.success
        )
        self.assertNotIn('Target_3', jobs[1].get('doing'))
        self.assertEqual(0, len(jobs[1].get('doing')))
        dawgie.pl.schedule.update(
            [('1.Target_3.test_15.D.sv.goat', True)], jobs[1], 1
        )
        _clean(jobs)
        self.assertEqual(len(jobs), 1)
        jobs.extend(dawgie.pl.schedule.next_job_batch())
        self.assertEqual(len(jobs), 1)
        for target in [
            'Target_0',
            'Target_1',
            'Target_2',
            'Target_4',
            'Target_5',
            'Target_6',
            'Target_7',
            'Target_8',
            'Target_9',
        ]:
            print('target:', target)
            dawgie.pl.schedule.complete(
                jobs[0], 1, target, {}, dawgie.pl.schedule.State.success
            )
            self.assertNotIn('Target_3', jobs[0].get('doing'))
            dawgie.pl.schedule.update(
                [(f'1.{target}.test_15.root.sv.goat', False)], jobs[0], 1
            )
            jobs.extend(dawgie.pl.schedule.next_job_batch())
            _clean(jobs)
            self.assertEqual(len(jobs), 1)
            pass
        jobs[0].set('status', dawgie.pl.schedule.State.running)
        jobs[0].get('do').clear()
        dawgie.pl.schedule.complete(
            jobs[0], 1, '__all__', {}, dawgie.pl.schedule.State.success
        )
        self.assertNotIn('__all__', jobs[0].get('doing'))
        dawgie.pl.schedule.update(
            [('1.__all__.test_15.E.goat', True)], jobs[0], 1
        )
        jobs.extend(dawgie.pl.schedule.next_job_batch())
        _clean(jobs)
        self.assertEqual(len(jobs), 0)
        return

    pass


def _clean(jobs):
    toBeRemoved = []
    for job in jobs:
        inque = 0
        for qn in ['do', 'doing', 'todo']:
            inque += len(job.get(qn))
        if inque == 0:
            toBeRemoved.append(job)
        pass
    for job in toBeRemoved:
        jobs.remove(job)
    return


def _mock_targets():
    return ['Target_' + c for c in '1234567890']


def _mock_task_name(*args, **kwds):
    return 'test_15'


def analysis(prefix: str, ps_hint: int = 0, runid: int = -1):
    return Analysis(prefix, ps_hint, runid, _al)


def events():
    return []


def regress(prefix: str, ps_hint: int = 0, target: str = '__none__'):
    return Regress(prefix, ps_hint, target, _rl)


def task(
    prefix: str, ps_hint: int = 0, runid: int = -1, target: str = '__none__'
):
    return Task(prefix, ps_hint, runid, target, _tl)


_al = []
_fb = []
_rl = []
_tl = []
_sv = StateVector()
_sv['goat'] = dawgie.Value()
_root = Work([], 'root', [])
_A = Work([], 'A', [dawgie.SV_REF(task, _root, _sv)])
_B = Work(_fb, 'B', [dawgie.SV_REF(task, _root, _sv)])
_C = Work([], 'C', [dawgie.SV_REF(task, _B, _sv)])
_D = Work([], 'D', [dawgie.SV_REF(task, _C, _sv), dawgie.SV_REF(task, _A, _sv)])
_E = Work([], 'E', [dawgie.SV_REF(regress, _D, _sv)])
_fb.append(dawgie.SV_REF(task, _C, _sv))
_al.append(_E)
_rl.append(_D)
_tl.extend([_root, _A, _B, _C])
