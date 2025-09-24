'''show that all DBs behave the same

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

import dawgie
import dawgie.db.shelve.enums
import dawgie.db.shelve.state
import dawgie.db.testdata
import dawgie.context
import os
import shutil
import tempfile
import unittest

from datetime import datetime as dt

# Save the actual work for another day, but this shows how to write one set
# of tests in DB then test each instance by two other objects that extend it.


class DB:
    @classmethod
    def setup(cls):
        dawgie.db.close()  # might be open from another TestSuite
        dawgie.db.open()
        for tsk, alg, sv, vn, v in dawgie.db.testdata.KNOWNS:
            dawgie.db.update(tsk, alg, sv, vn, v)
            pass
        for tgt, tsk, alg in dawgie.db.testdata.DATASETS:
            dawgie.db.connect(alg, tsk, tgt).update()
            pass
        for tsk, alg in dawgie.db.testdata.ASPECTS:
            dawgie.db.gather(alg, tsk).ds().update()
            pass
        for tsk, alg in dawgie.db.testdata.TIMELINES:
            dawgie.db.retreat(alg, tsk).ds().update()
            pass
        dawgie.db.close()
        return

    def test__prime_keys(self):
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db._prime_keys)
        dawgie.db.open()
        keys = dawgie.db._prime_keys()
        self.assertEqual(
            (
                dawgie.db.testdata.TSK_CNT
                * dawgie.db.testdata.SVN_CNT
                * dawgie.db.testdata.VAL_CNT
            ),
            len(keys),
        )
        return

    def test__prime_values(self):
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db._prime_values)
        dawgie.db.open()
        values = dawgie.db._prime_keys()
        self.assertEqual(
            (
                dawgie.db.testdata.TSK_CNT
                * dawgie.db.testdata.SVN_CNT
                * dawgie.db.testdata.VAL_CNT
            ),
            len(values),
        )
        return

    def test_add(self):
        dawgie.db.close()
        self.assertRaises(
            RuntimeError, dawgie.db.add, dawgie.db.testdata.TARGET
        )
        # actual testing of adding is done in test_targets because no way
        # to delete added targets
        return

    def test_archive(self):
        self.assertTrue(True)  # not testable in a reasonable sense
        return

    def test_connect(self):
        tgt, tsk, alg = dawgie.db.testdata.DATASETS[0]
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db.connect, alg, tsk, tgt)
        dawgie.db.open()
        self.assertIsNotNone(dawgie.db.connect(alg, tsk, tgt))
        dawgie.db.close()
        return

    def test_consistent(self):
        '''given a new data element, find all items after that can be promoted

        Pretend there isw a structure to the testdata: each aspect collects the
        regressions while the regression of the task. There are 6 taasks total
        where task 2 depnds on task 1, task 3 depends on tasks 1 and 2,
        task 4 depends on task 1. task 5 depends on task 3, and task 6 depnds
        on task 1.

        If task 2 is updated then it should update only tasks 3, 5, and 6.

        The structure is emulated in dawgie.db.testdata but since the DAG is
        never built, it is not important if it exists not because the database
        erases the structure anyway.

        Need to build the refs for consistency to reflect the structure being
        suggested in dawgie.db.testdata. The referneces here are completely
        artificial and would normally be built from the DAG. However this is
        test of the database not the DAG (see test_12).
        '''
        ins = []
        outs = []
        for tn, tsk, alg in dawgie.db.testdata.DATASETS[:2]:
            for sv in alg.sv:
                for vn, v in sv.items():
                    ins.append(
                        dawgie.db.REF(
                            dawgie.db.ID(tsk._name(), None),
                            dawgie.db.ID(alg.name(), alg),
                            dawgie.db.ID(sv.name(), sv),
                            dawgie.db.ID(vn, v),
                        )
                    )
                    pass
                pass
            pass
        tn, tsk, alg = dawgie.db.testdata.DATASETS[2]
        for sv in alg.sv:
            for vn, v in sv.items():
                outs.append(
                    dawgie.db.REF(
                        dawgie.db.ID(tsk._name(), None),
                        dawgie.db.ID(alg.name(), alg),
                        dawgie.db.ID(sv.name(), sv),
                        dawgie.db.ID(vn, v),
                    )
                )
                pass
            pass
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db.consistent, ins, outs, tn)
        dawgie.db.open()
        juncture = dawgie.db.consistent(ins, outs, tn)
        self.assertEqual(len(outs), len(juncture))
        tns, tsks, algs, svs, vs = set(), set(), set(), set(), set()
        for tnid, tskid, algid, svid, vid, _bn in juncture:
            tns.add(tnid)
            tsks.add(tskid)
            algs.add(algid)
            svs.add(svid)
            vs.add(vid)
            pass
        self.assertEqual(len(tns), 1)
        self.assertEqual(len(tsks), 1)
        self.assertEqual(len(algs), 1)
        self.assertEqual(len(svs), len(alg.sv))
        self.assertEqual(len(vs), len(outs))
        dawgie.db.close()
        return

    def test_copy(self):
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db.copy, None, None, None)
        return

    def test_gather(self):
        ans, anz = dawgie.db.testdata.ASPECTS[0]
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db.gather, anz, ans)
        dawgie.db.open()
        asp = dawgie.db.gather(anz, ans)
        self.assertIsNotNone(asp)
        self.assertEqual(0, len(asp))
        dawgie.db.close()
        return

    def test_metrics(self):
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db.metrics)
        dawgie.db.open()
        metrics = dawgie.db.metrics()
        self.assertEqual(dawgie.db.testdata.TSK_CNT, len(metrics))
        self.assertEqual(-2, metrics[-1].sv['task_memory'].value())
        dawgie.db.close()
        return

    def test_next(self):
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db.next)
        dawgie.db.open()
        self.assertEqual(dawgie.db.testdata.RUNID + 1, dawgie.db.next())
        dawgie.db.close()
        return

    def test_open(self):
        self.assertFalse(True)
        return

    def test_promote(self):
        ins = []
        outs = []
        for tn, tsk, alg in dawgie.db.testdata.DATASETS[:2]:
            for sv in alg.sv:
                for vn, v in sv.items():
                    ins.append(
                        dawgie.db.REF(
                            dawgie.db.ID(tsk._name(), None),
                            dawgie.db.ID(alg.name(), alg),
                            dawgie.db.ID(sv.name(), sv),
                            dawgie.db.ID(vn, v),
                        )
                    )
                    pass
                pass
            pass
        tn, tsk, alg = dawgie.db.testdata.DATASETS[2]
        for sv in alg.sv:
            for vn, v in sv.items():
                outs.append(
                    dawgie.db.REF(
                        dawgie.db.ID(tsk._name(), None),
                        dawgie.db.ID(alg.name(), alg),
                        dawgie.db.ID(sv.name(), sv),
                        dawgie.db.ID(vn, v),
                    )
                )
                pass
            pass
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db.consistent, ins, outs, tn)
        self.assertRaises(RuntimeError, dawgie.db.promote, (1, 1, 1), 1)
        dawgie.db.open()
        juncture = dawgie.db.consistent(ins, outs, tn)
        self.assertEqual(len(outs), len(juncture))
        tns, tsks, algs, svs, vs = set(), set(), set(), set(), set()
        for tnid, tskid, algid, svid, vid, _bn in juncture:
            tns.add(tnid)
            tsks.add(tskid)
            algs.add(algid)
            svs.add(svid)
            vs.add(vid)
            pass
        self.assertEqual(len(tns), 1)
        self.assertEqual(len(tsks), 1)
        self.assertEqual(len(algs), 1)
        self.assertEqual(len(svs), len(alg.sv))
        self.assertEqual(len(vs), len(outs))
        self.assertFalse(dawgie.db.promote(juncture, dawgie.db.testdata.RUNID))
        self.assertTrue(
            dawgie.db.promote(juncture, dawgie.db.testdata.RUNID + 12)
        )
        # clean up the promotion
        tgt, tsk, alg = dawgie.db.testdata.DATASETS[2]
        for sv in alg.state_vectors():
            for vn in sv.keys():
                r = dawgie.db.remove(
                    dawgie.db.testdata.RUNID + 12,
                    tgt,
                    tsk._name(),
                    alg.name(),
                    sv.name(),
                    vn,
                )
                pass
            pass
        dawgie.db.close()
        return

    def test_remove(self):
        dawgie.db.close()
        tgt, tsk, alg = dawgie.db.testdata.DATASETS[0]
        svn = alg.state_vectors()[0].name()
        vn = [k for k in alg.state_vectors()[0].keys()][0]
        self.assertRaises(
            RuntimeError,
            dawgie.db.remove,
            tsk._runid(),
            tgt,
            tsk._name(),
            alg.name(),
            svn,
            vn,
        )
        dawgie.db.open()
        removed = 0
        for sv in alg.state_vectors():
            for vn in sv:
                dawgie.db.remove(
                    tsk._runid(), tgt, tsk._name(), alg.name(), sv.name(), vn
                )
                removed += 1
        keys = dawgie.db._prime_keys()
        self.assertEqual(
            (
                dawgie.db.testdata.TSK_CNT
                * dawgie.db.testdata.SVN_CNT
                * dawgie.db.testdata.VAL_CNT
            )
            - removed,
            len(keys),
        )
        dawgie.db.connect(alg, tsk, tgt).update()
        keys = dawgie.db._prime_keys()
        self.assertEqual(
            (
                dawgie.db.testdata.TSK_CNT
                * dawgie.db.testdata.SVN_CNT
                * dawgie.db.testdata.VAL_CNT
            ),
            len(keys),
        )
        dawgie.db.close()
        return

    def test_reopen(self):
        self.assertFalse(True)
        return

    def test_reset(self):
        tgt, tsk, alg = dawgie.db.testdata.DATASETS[-1]
        print(tgt, tsk._name(), alg.name())
        alg._set_ver(dawgie.VERSION(100, 100, 100))
        for sv in alg.state_vectors():
            sv._set_ver(dawgie.VERSION(200, 200, 200))
            for val in sv.values():
                val._set_ver(dawgie.VERSION(400, 500, 600))
                pass
            pass
        print(type(alg.design()), alg.design())
        dawgie.db.close()
        self.assertRaises(
            RuntimeError,
            dawgie.db.reset,
            dawgie.db.testdata.RUNID,
            tgt,
            tsk._name(),
            alg,
        )
        dawgie.db.open()
        dawgie.db.reset(dawgie.db.testdata.RUNID, tgt, tsk._name(), alg)
        dawgie.db.close()
        print(type(alg.design()), alg.design())
        self.assertEqual(alg.design(), 1, 'design')
        self.assertEqual(alg.implementation(), 1, 'implementation')
        self.assertEqual(alg.bugfix(), 2, 'bugfix')
        for sv in alg.state_vectors():
            self.assertEqual(sv.design(), 1, 'design')
            self.assertEqual(sv.implementation(), 2, 'implementation')
            self.assertEqual(sv.bugfix(), 3, 'bugfix')
            # these should not have changed
            for val in sv.values():
                self.assertEqual(val.design(), 400, 'design')
                self.assertEqual(val.implementation(), 500, 'implementation')
                self.assertEqual(val.bugfix(), 600, 'bugfix')
                pass
            pass
        return

    def test_retreat(self):
        ret, reg = dawgie.db.testdata.TIMELINES[0]
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db.retreat, reg, ret)
        dawgie.db.open()
        tl = dawgie.db.retreat(reg, ret)
        self.assertIsNotNone(tl)
        self.assertEqual(0, len(tl))
        dawgie.db.close()
        return

    def test_targets(self):
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db.targets)
        dawgie.db.open()
        targets = dawgie.db.targets()
        self.assertEqual(1, len(targets))
        self.assertEqual(dawgie.db.testdata.TARGET, targets[0])
        self.assertTrue(dawgie.db.add(dawgie.db.testdata.TARGET))
        self.assertTrue(dawgie.db.add(dawgie.db.testdata.TARGET + '_a'))
        dawgie.db.close()
        return

    def test_trace(self):
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db.trace, ['a'])
        dawgie.db.open()
        last_alg = dawgie.db.testdata.ALG_CNT - 1
        tans = [
            'Analysis_00.Analyzer_{:02d}'.format(last_alg),
            'Regress_01.Regression_{:02d}'.format(last_alg),
            'Task_02.Algorithm_{:02d}'.format(last_alg),
        ]
        runids = dawgie.db.trace(tans)
        dawgie.db.close()
        self.assertEqual(
            2 if dawgie.db.testdata.TARGET + '_a' in runids else 1, len(runids)
        )
        self.assertEqual(3, len(runids[dawgie.db.testdata.TARGET]))
        self.assertEqual(17, runids[dawgie.db.testdata.TARGET][tans[0]])
        self.assertEqual(0, runids[dawgie.db.testdata.TARGET][tans[1]])
        self.assertEqual(17, runids[dawgie.db.testdata.TARGET][tans[2]])
        return

    def test_update(self):
        dawgie.db.close()
        tgt, tsk, alg = dawgie.db.testdata.DATASETS[0]
        svn = alg.state_vectors()[0].name()
        vn = [k for k in alg.state_vectors()[0].keys()][0]
        self.assertRaises(
            RuntimeError,
            dawgie.db.remove,
            tsk._runid(),
            tgt,
            tsk._name(),
            alg.name(),
            svn,
            vn,
        )
        dawgie.db.open()
        removed = 0
        for sv in alg.state_vectors():
            for vn in sv:
                dawgie.db.remove(
                    tsk._runid(), tgt, tsk._name(), alg.name(), sv.name(), vn
                )
                removed += 1
        keys = dawgie.db._prime_keys()
        self.assertEqual(
            (
                dawgie.db.testdata.TSK_CNT
                * dawgie.db.testdata.SVN_CNT
                * dawgie.db.testdata.VAL_CNT
            )
            - removed,
            len(keys),
        )
        dawgie.db.connect(alg, tsk, tgt).update()
        keys = dawgie.db._prime_keys()
        self.assertEqual(
            (
                dawgie.db.testdata.TSK_CNT
                * dawgie.db.testdata.SVN_CNT
                * dawgie.db.testdata.VAL_CNT
            ),
            len(keys),
        )
        dawgie.db.close()
        return

    def test_versions(self):
        dawgie.db.close()
        self.assertRaises(RuntimeError, dawgie.db.versions)
        dawgie.db.open()
        tskv, algv, svv, vv = dawgie.db.versions()
        self.assertEqual(dawgie.db.testdata.TSK_CNT, len(tskv))
        self.assertEqual(
            (dawgie.db.testdata.TSK_CNT * dawgie.db.testdata.ALG_CNT), len(algv)
        )
        self.assertEqual(
            (
                dawgie.db.testdata.TSK_CNT
                * dawgie.db.testdata.ALG_CNT
                * dawgie.db.testdata.SVN_CNT
            ),
            len(svv),
        )
        self.assertEqual(
            (
                dawgie.db.testdata.TSK_CNT
                * dawgie.db.testdata.ALG_CNT
                * dawgie.db.testdata.SVN_CNT
                * dawgie.db.testdata.VAL_CNT
            ),
            len(vv),
        )
        return

    def test_locks(self):
        self.assertTrue(False)
        return

    pass


# to test postgres:
#   docker pull postgres:latest
#   docker run --detach --env POSTGRES_PASSWORD=password --env POSTGRES_USER=tester --env POSTGRES_HOST_AUTH_METHOD=trust --name postgres --publish 5432:5432 --rm  postgres:latest
#   docker exec -i postgres createdb -U tester testspace
#
# notes:
#   takes about 5 minutes to load the database
#   once loaded it can simply be re-used (no reason to dump and start again)
class Post(DB, unittest.TestCase):
    @classmethod
    def setUpClass(cls, root=None):
        cls.root = root if root else tempfile.mkdtemp()
        if not os.path.isdir(os.path.join(cls.root, 'db')):
            os.mkdir(os.path.join(cls.root, 'db'))
            os.mkdir(os.path.join(cls.root, 'dbs'))
            os.mkdir(os.path.join(cls.root, 'logs'))
            os.mkdir(os.path.join(cls.root, 'stg'))
        dawgie.context.db_host = 'localhost'
        dawgie.context.db_impl = 'post'
        dawgie.context.db_name = 'testspace'
        dawgie.context.db_path = 'tester:password'
        dawgie.context.db_port = 5432
        dawgie.context.data_dbs = os.path.join(cls.root, 'dbs')
        dawgie.context.data_log = os.path.join(cls.root, 'logs')
        dawgie.context.data_stg = os.path.join(cls.root, 'stg')
        dawgie.db_rotate_path = os.path.join(cls.root, 'db')
        if not root:
            DB.setup()
        return

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, True)
        return

    def test_close(self):
        dawgie.db.close()
        self.assertFalse(dawgie.db.post._db)
        dawgie.db.open()
        dawgie.db.close()
        self.assertFalse(dawgie.db.post._db)
        return

    def test_copy(self):
        self.assertRaises(NotImplementedError, dawgie.db.copy, 1, 2, 3)
        return

    def test_locks(self):
        self.assertTrue(True)  # locks not used in postgres
        return

    def test_open(self):
        dawgie.db.close()
        self.assertFalse(dawgie.db.post._db)
        dawgie.db.open()
        self.assertTrue(dawgie.db.post._db)
        dawgie.db.close()
        self.assertFalse(dawgie.db.post._db)
        return

    def test_reopen(self):
        dawgie.db.close()
        self.assertFalse(dawgie.db.post._db)
        dawgie.db.reopen()
        self.assertTrue(dawgie.db.post._db)
        dawgie.db.close()
        self.assertFalse(dawgie.db.post._db)
        return

    pass


class Shelve(DB, unittest.TestCase):
    @classmethod
    def setUpClass(cls, root=None):
        cls.root = root if root else tempfile.mkdtemp()
        if not os.path.isdir(os.path.join(cls.root, 'db')):
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
        dawgie.db_rotate_path = dawgie.context.db_path
        cls._acquire = getattr(dawgie.db.shelve.comms, 'acquire')
        cls._delay_copy = (dawgie.db.shelve.comms.Worker, '_delay_copy')
        cls._do = getattr(dawgie.db.shelve.comms.Connector, '_Connector__do')
        cls._release = getattr(dawgie.db.shelve.comms, 'release')
        cls._send = getattr(dawgie.db.shelve.comms.Worker, '_send')
        setattr(dawgie.db.shelve.comms, 'acquire', mock_acquire)
        setattr(dawgie.db.shelve.comms.Worker, '_delay_copy', mock_delay_copy)
        setattr(dawgie.db.shelve.comms.Connector, '_Connector__do', mock_do)
        setattr(dawgie.db.shelve.comms, 'release', mock_release)
        setattr(dawgie.db.shelve.comms.Worker, '_send', mock_send)
        if not root:
            DB.setup()
        return

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, True)
        setattr(dawgie.db.shelve.comms, 'acquire', cls._acquire)
        setattr(dawgie.db.shelve.comms.Worker, '_delay_copy', cls._delay_copy)
        setattr(dawgie.db.shelve.comms.Connector, '_Connector__do', cls._do)
        setattr(dawgie.db.shelve.comms, 'release', cls._release)
        setattr(dawgie.db.shelve.comms.Worker, '_send', cls._send)
        return

    def test_close(self):
        dawgie.db.close()
        self.assertFalse(dawgie.db.shelve.state.DBI().is_open)
        dawgie.db.open()
        dawgie.db.close()
        self.assertFalse(dawgie.db.shelve.state.DBI().is_open)
        return

    def test_consistent(self):
        self.assertRaises(NotImplementedError, dawgie.db.consistent, [], [], '')
        return

    def test_copy(self):
        super().test_copy()
        root = os.path.join(self.root, 'connector')
        os.makedirs(root)
        dawgie.db.open()
        retval = dawgie.db.copy(
            root, dawgie.db.shelve.enums.Method.connector, 'localhost'
        )
        self.assertEqual(0, retval)
        dawgie.db.close()
        return

    def test_locks(self):
        dawgie.db.close()
        dawgie.db.open()
        self.assertEqual(dawgie.db.view_locks(), {'tasks': []})
        dawgie.db.close()
        return

    def test_open(self):
        dawgie.db.close()
        self.assertFalse(dawgie.db.shelve.state.DBI().is_open)
        dawgie.db.open()
        self.assertTrue(dawgie.db.shelve.state.DBI().is_open)
        dawgie.db.close()
        self.assertFalse(dawgie.db.shelve.state.DBI().is_open)
        return

    def test_promote(self):
        self.assertRaises(NotImplementedError, dawgie.db.promote, [], 1)
        return

    def test_reopen(self):
        dawgie.db.close()
        self.assertFalse(dawgie.db.shelve.state.DBI().is_open)
        dawgie.db.reopen()
        self.assertTrue(dawgie.db.shelve.state.DBI().is_open)
        self.assertTrue(dawgie.db.shelve.state.DBI().is_reopened)
        dawgie.db.close()
        self.assertFalse(dawgie.db.shelve.state.DBI().is_open)
        return

    pass


def mock_acquire(name):
    return True


def mock_release(s):
    return True


do_response = [None]


def mock_do(self, request):
    # print ('mock do', request)
    import dawgie.db.shelve.comms

    dawgie.db.shelve.comms.Worker(None).do(request)
    return do_response[0]


def mock_delay_copy(self, request_value):
    self._do_copy(request_value)
    return


def mock_send(self, response):
    do_response[0] = response
    return
