''' show that all DBs behave the same

COPYRIGHT:
Copyright (c) 2015-2021, California Institute of Technology ("Caltech").
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
        dawgie.db.open()
        for tsk,alg,sv,vn,v in dawgie.db.testdata.KNOWNS:
            dawgie.db.update (tsk, alg, sv, vn, v)
            pass
        for tgt,tsk,alg in dawgie.db.testdata.DATASETS:
            dawgie.db.connect (alg, tsk, tgt).update()
            pass
        for tsk,alg in dawgie.db.testdata.ASPECTS:
            dawgie.db.gather (alg, tsk).ds().update()
            pass
        for tsk,alg in dawgie.db.testdata.TIMELINES:
            dawgie.db.retreat (alg, tsk).ds().update()
            pass
        dawgie.db.close()
        return

    def test__prime_keys(self):
        dawgie.db.close()
        self.assertRaises (RuntimeError, dawgie.db._prime_keys)
        dawgie.db.open()
        keys = dawgie.db._prime_keys()
        self.assertEqual ((dawgie.db.testdata.TSK_CNT *
                           dawgie.db.testdata.SVN_CNT *
                           dawgie.db.testdata.VAL_CNT), len(keys))
        return

    def test__prime_values(self):
        dawgie.db.close()
        self.assertRaises (RuntimeError, dawgie.db._prime_values)
        dawgie.db.open()
        values = dawgie.db._prime_keys()
        self.assertEqual ((dawgie.db.testdata.TSK_CNT *
                           dawgie.db.testdata.SVN_CNT *
                           dawgie.db.testdata.VAL_CNT), len(values))
        return

    def test_archive(self):
        self.assertTrue (True)  # not testable in a reasonable sense
        return

    def test_close(self):
        dawgie.db.close()
        self.assertFalse (dawgie.db.post._db)
        dawgie.db.open()
        dawgie.db.close()
        self.assertFalse (dawgie.db.post._db)
        return

    def test_connect(self):
        tgt,tsk,alg = dawgie.db.testdata.DATASETS[0]
        dawgie.db.close()
        self.assertRaises (RuntimeError, dawgie.db.connect, alg, tsk, tgt)
        dawgie.db.open()
        self.assertIsNotNone (dawgie.db.connect (alg, tsk, tgt))
        dawgie.db.close()
        return

    def test_consistent(self):
        self.assertTrue (False)
        return

    def test_copy(self):
        self.assertTrue (False)
        return

    def test_gather(self):
        ans,anz = dawgie.db.testdata.ASPECTS[0]
        dawgie.db.close()
        self.assertRaises (RuntimeError, dawgie.db.gather, anz, ans)
        dawgie.db.open()
        self.assertIsNotNone (dawgie.db.gather (anz, ans))
        dawgie.db.close()
        return

    def test_metrics(self):
        dawgie.db.close()
        self.assertRaises (RuntimeError, dawgie.db.metrics)
        dawgie.db.open()
        self.assertEqual (dawgie.db.testdata.TSK_CNT, len (dawgie.db.metrics()))
        dawgie.db.close()
        return

    def test_next(self):
        dawgie.db.close()
        self.assertRaises (RuntimeError, dawgie.db.next)
        dawgie.db.open()
        self.assertEqual (dawgie.db.testdata.RUNID+1, dawgie.db.next())
        dawgie.db.close()
        return

    def test_open(self):
        dawgie.db.close()
        self.assertFalse (dawgie.db.post._db)
        dawgie.db.open()
        self.assertTrue (dawgie.db.post._db)
        dawgie.db.close()
        self.assertFalse (dawgie.db.post._db)
        return

    def test_promote(self):
        self.assertTrue (False)
        return

    def test_remove(self):
        dawgie.db.close()
        tgt,tsk,alg = dawgie.db.testdata.DATASETS[0]
        svn = alg.state_vectors()[0].name()
        vn = [k for k in alg.state_vectors()[0].keys()][0]
        self.assertRaises (RuntimeError, dawgie.db.remove,
                           tsk._runid(), tgt, tsk._name(), alg.name(), svn, vn)
        dawgie.db.open()
        dawgie.db.remove (tsk._runid(), tgt, tsk._name(), alg.name(), svn, vn)
        keys = dawgie.db._prime_keys()
        self.assertEqual ((dawgie.db.testdata.TSK_CNT *
                           dawgie.db.testdata.SVN_CNT *
                           dawgie.db.testdata.VAL_CNT) - 1, len(keys))
        dawgie.db.connect (alg, tsk, tgt).update()
        keys = dawgie.db._prime_keys()
        self.assertEqual ((dawgie.db.testdata.TSK_CNT *
                           dawgie.db.testdata.SVN_CNT *
                           dawgie.db.testdata.VAL_CNT), len(keys))
        dawgie.db.close()
        return

    def test_reopen(self):
        dawgie.db.close()
        self.assertFalse (dawgie.db.post._db)
        dawgie.db.reopen()
        self.assertTrue (dawgie.db.post._db)
        dawgie.db.close()
        self.assertFalse (dawgie.db.post._db)
        return

    def test_retreat(self):
        ret,reg = dawgie.db.testdata.TIMELINES[0]
        dawgie.db.close()
        self.assertRaises (RuntimeError, dawgie.db.retreat, reg, ret)
        dawgie.db.open()
        self.assertIsNotNone (dawgie.db.retreat (reg, ret))
        dawgie.db.close()
        return

    def test_targets(self):
        dawgie.db.close()
        self.assertRaises (RuntimeError, dawgie.db.targets)
        dawgie.db.open()
        targets = dawgie.db.targets()
        self.assertEqual (1, len(targets))
        self.assertEqual (dawgie.db.testdata.TARGET, targets[0])
        return

    def test_trace(self):
        dawgie.db.close()
        self.assertRaises (RuntimeError, dawgie.db.trace, ['a'])
        dawgie.db.open()
        last_alg = dawgie.db.testdata.ALG_CNT-1
        tans = ['Analysis_00.Analyzer_{:02d}'.format (last_alg),
                'Regress_01.Regression_{:02d}'.format (last_alg),
                'Task_02.Algorithm_{:02d}'.format (last_alg)]
        runids = dawgie.db.trace (tans)
        dawgie.db.close()
        self.assertEqual (1, len(runids))
        self.assertEqual (3, len(runids[dawgie.db.testdata.TARGET]))
        self.assertEqual (17, runids[dawgie.db.testdata.TARGET][tans[0]])
        self.assertEqual (0, runids[dawgie.db.testdata.TARGET][tans[1]])
        self.assertEqual (17, runids[dawgie.db.testdata.TARGET][tans[2]])
        return

    def test_update (self):
        dawgie.db.close()
        tgt,tsk,alg = dawgie.db.testdata.DATASETS[0]
        svn = alg.state_vectors()[0].name()
        vn = [k for k in alg.state_vectors()[0].keys()][0]
        self.assertRaises (RuntimeError, dawgie.db.remove,
                           tsk._runid(), tgt, tsk._name(), alg.name(), svn, vn)
        dawgie.db.open()
        dawgie.db.remove (tsk._runid(), tgt, tsk._name(), alg.name(), svn, vn)
        keys = dawgie.db._prime_keys()
        self.assertEqual ((dawgie.db.testdata.TSK_CNT *
                           dawgie.db.testdata.SVN_CNT *
                           dawgie.db.testdata.VAL_CNT) - 1, len(keys))
        dawgie.db.connect (alg, tsk, tgt).update()
        keys = dawgie.db._prime_keys()
        self.assertEqual ((dawgie.db.testdata.TSK_CNT *
                           dawgie.db.testdata.SVN_CNT *
                           dawgie.db.testdata.VAL_CNT), len(keys))
        dawgie.db.close()
        return

    @unittest.skip ('takes too long while developing other tests')
    def test_versions(self):
        dawgie.db.close()
        self.assertRaises (RuntimeError, dawgie.db.versions)
        dawgie.db.open()
        tskv,algv,svv,vv = dawgie.db.versions()
        self.assertEqual (dawgie.db.testdata.TSK_CNT, len(tskv))
        self.assertEqual ((dawgie.db.testdata.TSK_CNT *
                           dawgie.db.testdata.ALG_CNT), len(algv))
        self.assertEqual ((dawgie.db.testdata.TSK_CNT *
                           dawgie.db.testdata.ALG_CNT *
                           dawgie.db.testdata.SVN_CNT), len(svv))
        self.assertEqual ((dawgie.db.testdata.TSK_CNT *
                           dawgie.db.testdata.ALG_CNT *
                           dawgie.db.testdata.SVN_CNT *
                           dawgie.db.testdata.VAL_CNT), len(vv))
        return

    def test_locks(self):
        self.assertTrue (False)
        return
    pass

# to test postgres:
#   docker pull postgres:13.3
#   docker network create cit
#   docker run --detach --env POSTGRES_PASSWORD=password --env POSTGRES_USER=tester --name postgres --network cit --rm  postgres:13.3
#   docker exec -i postgres createdb -U tester testspace
#   CIT_NETWORK=cit .ci/check_03.sh ; git checkout .ci/status.txt
#   docker network rm cit
#
# notes:
#   takes about 5 minutes to load the database
#   once loaded it can simply be re-used (no reason to dump and start again)
#unittest.skip ('no automatic way to build postgres database')
class Post(DB,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()
        os.mkdir (os.path.join (cls.root, 'db'))
        os.mkdir (os.path.join (cls.root, 'dbs'))
        os.mkdir (os.path.join (cls.root, 'logs'))
        os.mkdir (os.path.join (cls.root, 'stg'))
        dawgie.context.db_host = 'postgres'
        dawgie.context.db_impl = 'post'
        dawgie.context.db_name = 'testspace'
        dawgie.context.db_path = 'tester:password'
        dawgie.context.db_port = 5432
        dawgie.context.data_dbs = os.path.join (cls.root, 'dbs')
        dawgie.context.data_log = os.path.join (cls.root, 'logs')
        dawgie.context.data_stg = os.path.join (cls.root, 'stg')
        dawgie.db_rotate_path = os.path.join (cls.root, 'db')
        DB.setup()
        return

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree (cls.root, True)
        return

    def test_copy(self):
        self.assertRaises (NotImplementedError, dawgie.db.copy, 1, 2, 3)
        return

    def test_locks(self):
        self.assertTrue (True)  # locks not used in postgres
        return
    pass

@unittest.skip ('current shelf is not a true replacement for postgres')
class Shelf(DB,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()
        os.mkdir (os.path.join (cls.root, 'db'))
        os.mkdir (os.path.join (cls.root, 'dbs'))
        os.mkdir (os.path.join (cls.root, 'logs'))
        os.mkdir (os.path.join (cls.root, 'stg'))
        dawgie.context.db_impl = 'shelf'
        dawgie.context.db_name = 'testspace'
        dawgie.context.db_path = os.path.join (cls.root, 'db')
        dawgie.context.data_dbs = os.path.join (cls.root, 'dbs')
        dawgie.context.data_log = os.path.join (cls.root, 'logs')
        dawgie.context.data_stg = os.path.join (cls.root, 'stg')
        dawgie.db_rotate_path = dawgie.context.db_path
        cls._acquire = getattr (dawgie.db.shelf.Connector, '_keys')
        cls._do = getattr (dawgie.db.shelf.Connector, '_Connector__do')
        cls._release = getattr (dawgie.db.shelf.Connector, '_keys')
        cls._send = getattr (dawgie.db.shelf.Worker, '_send')
        setattr (dawgie.db.shelf.Connector, '_acquire', mock_acquire)
        setattr (dawgie.db.shelf.Connector, '_Connector__do', mock_do)
        setattr (dawgie.db.shelf.Connector, '_release', mock_release)
        setattr (dawgie.db.shelf.Worker, '_send', mock_send)
        DB.setup()
        return

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree (cls.root, True)
        setattr (dawgie.db.shelf.Connector, '_acquire', cls._acquire)
        setattr (dawgie.db.shelf.Connector, '_Connector__do', cls._do)
        setattr (dawgie.db.shelf.Connector, '_release', cls._release)
        setattr (dawgie.db.shelf.Worker, '_send', cls._send)
        return
    pass

def mock_acquire (self, name): return True
def mock_release (self, s): return True

do_response = [None]
def mock_do (self, request):
    # print ('mock do', request)
    import dawgie.db.shelf
    dawgie.db.shelf.Worker(None).do (request)
    return do_response[0]

def mock_send (self, response):
    do_response[0] = response
    return
