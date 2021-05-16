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

# Save the actual work for another day, but this shows how to write one set
# of tests in DB then test each instance by two other objects that extend it.

import dawgie
import dawgie.db.testdata
import dawgie.context
import unittest

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
        for juncture in dawgie.db.testdata.testdata.JUNCTURES:
            dawgie.db.promote (juncture)
            pass
        dawgie.db.close()
        return

    def test__prime_keys(self):
        return

    def test__prime_values(self):
        return

    def test_archive(self):
        self.assertTrue (True)
        return

    def test_close(self):
        return

    def test_connect(self):
        return

    def test_consistent(self):
        return

    def test_copy(self):
        return

    def test_gather(self):
        return

    def test_metrics(self):
        return

    def test_next(self):
        return

    def test_open(self):
        return

    def test_promote(self):
        return

    def test_remove(self):
        return

    def test_reopen(self):
        return

    def test_retreat(self):
        return

    def test_targets(self):
        return

    def test_trace(self):
        return

    def test_update (self):
        return

    def test_versions(self):
        return

    def test_locks(self):
        return
    pass

@unittest.skip ('no generic way to build postgres database')
class Post(DB,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dawgie.context.db_impl = 'post'
        DB.setup()
        return
    pass

@unittest.skip ('current shelf is not a true replacement for postgres')
class Shelf(DB,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dawgie.context.db_impl = 'shelf'
        DB.setup()
        return
    pass
