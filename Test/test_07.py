'''

COPYRIGHT:
Copyright (c) 2015-2022, California Institute of Technology ("Caltech").
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
import dawgie.context
import dawgie.db
import dawgie.db.shelve.comms
import os
import shutil
import tempfile
import unittest

class aBar(dawgie.Analyzer):
    def __init__(self):
        dawgie.Analyzer.__init__(self)
        self._product = aSV()
        self._version_ = dawgie.VERSION(1,1,1)
        return

    def name(self): return 'bar'
    def run (self, aspects): return
    def state_vectors(self): return [self._product]
    def traits(self): return []
    pass

class aFoo(dawgie.Analysis):
    def list(self): return [aBar()]
    pass

class aSV(dawgie.StateVector):
    def __init__ (self):
        dawgie.StateVector.__init__(self)
        self['oops'] = aV()
        self['snafu'] = aV()
        self._version_ = dawgie.VERSION(1,1,1)
        return
    def name(self): return 'and'
    pass

class aV(dawgie.Value):
    def __init__(self):
        dawgie.Value.__init__(self)
        self._version_ = dawgie.VERSION(1,1,1)
        return
    def features(self): return []
    pass

class Shelve(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()
        print (cls.root)
        for subdir in ['db', 'dbs', 'stg']: os.makedirs(os.path.join
                                                        (cls.root, subdir))
        dawgie.context.db_impl = 'shelve'
        dawgie.context.db_path = os.path.join (cls.root, 'db')
        dawgie.context.data_dbs = os.path.join (cls.root, 'dbs')
        dawgie.context.data_log = os.path.join (cls.root, 'logs')
        dawgie.context.data_stg = os.path.join (cls.root, 'stg')
        dawgie.db_rotate_path = dawgie.context.db_path
        dawgie.db.open()
        base = aFoo('foo', 0, 1)
        cls._acquire = getattr (dawgie.db.shelve.comms, 'acquire')
        cls._do = getattr (dawgie.db.shelve.comms.Connector, '_Connector__do')
        cls._release = getattr (dawgie.db.shelve.comms, 'release')
        cls._send = getattr (dawgie.db.shelve.comms.Worker, '_send')
        setattr (dawgie.db.shelve.comms, 'acquire', mock_acquire)
        setattr (dawgie.db.shelve.comms.Connector, '_Connector__do', mock_do)
        setattr (dawgie.db.shelve.comms, 'release', mock_release)
        setattr (dawgie.db.shelve.comms.Worker, '_send', mock_send)
        dawgie.db.update (base,base.list()[0],base.list()[0].state_vectors()[0],
                          'oops', base.list()[0].state_vectors()[0]['oops'])
        dawgie.db.update (base,base.list()[0],base.list()[0].state_vectors()[0],
                          'snafu', base.list()[0].state_vectors()[0]['snafu'])
        connection = dawgie.db.connect (base.list()[0], base, '__all__')
        connection.update()
        return

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree (cls.root)
        setattr (dawgie.db.shelve.comms, 'acquire', cls._acquire)
        setattr (dawgie.db.shelve.comms.Connector, '_Connector__do', cls._do)
        setattr (dawgie.db.shelve.comms, 'release', cls._release)
        setattr (dawgie.db.shelve.comms.Worker, '_send', cls._send)
        return

    def test_issue_16(self):
        '''target list does not contain __all__

        Reported as in the state when __all__ is the only known target from a
        state vector save, it does not show up in the search targets or command
        page. It does, however, show up in the primary table.

        The two locations noted:
            1. targets in database search
            2. targets in command
        should be full lists and not trunctated lists.

        Even forcing __all__ into the search fails.
        '''
        full_list = dawgie.db.targets (True)
        print (full_list)
        self.assertTrue ('__all__' in full_list)
        return
    pass

def mock_acquire (name): return True
def mock_release (s): return True

do_response = [None]
def mock_do (self, request):
    print ('mock do', request)
    import dawgie.db.shelve
    dawgie.db.shelve.comms.Worker(None).do (request)
    return do_response[0]

def mock_send (self, response):
    do_response[0] = response
    return
