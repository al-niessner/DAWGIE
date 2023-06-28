'''the twisted portion of the shelve implementation

--
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

import collections
import dawgie.db.lockview
import dawgie.context
import dawgie.security
import logging; log = logging.getLogger(__name__)
import os
import pickle
import struct
import twisted.internet.protocol
import twisted.internet.reactor
import twisted.internet.task
import twisted.internet.threads

from . import util
from .enums import Func
from .enums import Method
from .enums import Mutex
from .enums import Table
from .state import DBI

COMMAND = collections.namedtuple('COMMAND', ['func','keyset','table','value'])
KEYSET = collections.namedtuple('KEYSET', ['name', 'parent', 'ver'])

class Connector:  # pylint: disable=too-few-public-methods
    # this class is meant to be extendend like an abstract class
    def _copy (self, dst, method):
        return self.__do (COMMAND(Func.dbcopy, None, None, [method,dst]))

    @staticmethod
    def __do (request):
        s = dawgie.security.connect ((dawgie.context.db_host,
                                      dawgie.context.db_port))
        msg = pickle.dumps (request, pickle.HIGHEST_PROTOCOL)
        s.sendall (struct.pack ('>I', len(msg)) + msg)
        buf = b''
        log.debug ('Connector.__do() - sending command')
        while len (buf) < 4: buf += s.recv(4 - len (buf))
        l = struct.unpack ('>I', buf)[0]
        buf = b''
        log.debug ('Connector.__do() - receiving command')
        while len (buf) < l: buf += s.recv(l - len (buf))
        s.close()
        return pickle.loads (buf)

    def _get_prime (self, key:(int,int,int,int,int,int)):
        ret = self.__do (COMMAND(Func.get, key, Table.prime, None))
        ret = dawgie.db.util.decode (ret)
        return ret

    def _prime_keys (self):
        log.debug ('Connector._prime_keys() - get prime keys')
        return util.prime_keys(self._table (Table.prime))

    def _set_prime (self, key:(int,int,int,int,int,int), value:dawgie.Value):
        value = dawgie.db.util.encode (value)
        return self.__do (COMMAND(Func.set, key, Table.prime, value))

    def _table (self, table)->{}:
        return self.__do (COMMAND(Func.table, None, table, None))

    # pylint: disable=too-many-arguments
    def _update_cmd (self, name, parent, table, value, ver):
        keyset = KEYSET(name, parent, ver)
        return self.__do (COMMAND(Func.upd, keyset, table, value))
    # pylint: enable=too-many-arguments

    # public methods for modules in this package
    def copy (self, dst, method):
        '''public method for .impl'''
        return self._copy (dst, method)
    pass

class DBSerializer(twisted.internet.protocol.Factory):
    def buildProtocol (self, addr): return Worker(addr)
    @staticmethod
    def open():
        try: twisted.internet.reactor.listenTCP(int(dawgie.context.db_port),
                                                DBSerializer(),
                                                dawgie.context.worker_backlog)
        except twisted.internet.error.CannotListenError:\
               log.warning("Address already in use.")
        return
    pass

class Worker(twisted.internet.protocol.Protocol):
    def __init__ (self, address):
        twisted.internet.protocol.Protocol.__init__(self)
        self.__buf = {'actual':len(struct.pack('>I',0)),'data':b'','expected':0}
        # really is used so pylint: disable=unused-private-member
        self.__handshake = dawgie.security.TwistedWrapper(self, address)
        # really is used so pylint: enable=unused-private-member
        self.__has_lock = False
        self.__id_name = 'unknown'
        self.__looping_call = twisted.internet.task.LoopingCall(self._do_acquire)
        self.__looping_call_stopped = False
        self.__connection_lost = False
        return

    def _send (self, response):
        msg = pickle.dumps (response, pickle.HIGHEST_PROTOCOL)
        self.transport.write (struct.pack ('>I', len (msg)) + msg)
        return

    # pylint: disable=signature-differs
    def connectionLost (self, reason):
        self.__connection_lost = True

        if self.__looping_call.running and not self.__looping_call_stopped:
            log.debug("ConnectionLost: Stopping looping call.")
            twisted.internet.reactor.callLater(1, self.__looping_call.stop)
            self.__looping_call_stopped = True
            pass

        if self.__has_lock:
            log.debug("ConnectionLost: Release lock after losing connection =(")
            self._unlock_db()
            pass
        return

    def dataReceived (self, data):
        self.__buf['data'] += data
        length = self.__buf['actual'] if self.__buf['expected'] is None else self.__buf['expected']
        while length <= len (self.__buf['data']):
            if self.__buf['expected'] is None:
                self.__buf['expected'] = struct.unpack ('>I', self.__buf['data'][:length])[0]
                self.__buf['data'] = self.__buf['data'][length:]
            else:
                request = pickle.loads (self.__buf['data'][:length])
                self.__buf['data'] = self.__buf['data'][length:]
                self.__buf['expected'] = None

                if request.func not in [Func.acquire,Func.dbcopy]:
                    try: self.do (request)
                    except ImportError: log.excpetion ('Had a problem unpickling an input so aborting connection and moving forward.')
                    finally: self.transport.loseConnection()
                else:
                    try: self.do (request)
                    except ImportError:
                        log.excpetion ('Had a problem unpickling an input so aborting connection and moving forward.')
                        self.transport.loseConnection()
                        pass
                    pass
                pass

            length = self.__buf['actual'] if self.__buf['expected'] is None else self.__buf['expected']
            pass
        return

    def do (self, request):
        # pylint: disable=too-many-branches
        if request.func == Func.acquire:
            self.__id_name = request.value
            log.debug("Inside worker(%s): Acquire",
                                               self.__id_name)
            # Lock Request Begin
            DBI().task_engine.add_task(self.__id_name,
                                       dawgie.db.lockview.LockRequest.lrqb)
            self.__looping_call.start(3)
        elif request.func == Func.dbcopy:
            self._delay_copy (request.value)
        elif request.func == Func.get:
            key = util.construct (**request.keyset)
            self._send (DBI().tables[request.table.value][key])
        elif request.func == Func.release:
            log.debug("Inside worker: Release")
            self._do_release()
        elif request.func == Func.set:
            if request.table != Table.prime:
                log.error ('Cannot set non-prime table. Muse use updatt_cmd')
                return

            value,exists = dawgie.db.util.move(*request.value)
            key = str(request.keyset)
            DBI().tables[request.table.value][key] = value
            self._send (exists)
        elif request.func == Func.table:
            log.debug ('Worker.do() - received request for table')
            log.debug ('Worker.do() - table %s', request.table.name)
            log.debug ('Worker.do() - table size %d',
                       len (DBI().tables[request.table.value]))
            self._send(dict(DBI().tables[request.table.value]))
        elif request.func == Func.upd:
            if request.table.value == Table.prime:
                log.error ('Cannot update prime. Must use set')
                return

            kwds = request.keyset._asdict()
            if kwds['ver']: kwds['ver'] = util.LocalVersion(kwds['ver'])
            response = util.append (table=DBI().tables[request.table.value],
                                    index=DBI().indices[request.table.value],
                                    **kwds)
            self._send (response)
        else: log.error ('Did not understand %s', str (request))
        return

    def _do_acquire(self):
        if self.__looping_call_stopped: return
        if self.__connection_lost:
            log.debug("_do_acquire(%s): connection has already been lost",
                      self.__id_name)
            return

        log.debug("_do_acquire(%s): checking lock status...", self.__id_name)

        s = self._get_db_lock_status()
        if s == Mutex.unlock:
            log.debug("_do_acquire(%s): lock is unlocked!", self.__id_name)
            self._lock_db()
            log.debug("_do_acquire(%s): lock is now locked!", self.__id_name)
            log.debug("_do_acquire(%s): calling stop", self.__id_name)
            twisted.internet.reactor.callLater(1, self.__looping_call.stop)
            self.__looping_call_stopped = True
            # Lock Request End
            DBI().task_engine.add_task(self.__id_name,
                                       dawgie.db.lockview.LockRequest.lrqe)

            # Lock Acquire Begin
            DBI().task_engine.add_task(self.__id_name,
                                       dawgie.db.lockview.LockRequest.laqb)
            pass
        self._send(s)
        return

    def _delay_copy (self, request_value):
        twisted.internet.threads.deferToThread(self._do_copy, request_value)
        return

    def _do_copy(self, param):
        method = param[0]
        dst = param[1]
        src = dawgie.context.db_path
        tmpdst = util.mkStgDir()
        retValue = None
        log.debug("_do_copy: Acquiring. dst -> %s", dst)
        lok = acquire('copy')

        try:
            log.debug("_do_copy: Got lok")
            src = dawgie.context.db_path

            if os.path.exists(src):
                DBI().close()
                if method == Method.connector:
                    DBI().open()
                    retValue = DBI().copy()
                else:
                    r = os.system(f"rsync --delete -ax {src}/ {tmpdst}/")
                    retValue = tmpdst if r == 0 else None
                    DBI().open()
                    pass
            else:
                log.error ('%s does not exists.', src)
                retValue = None
        finally:
            if not DBI().is_open: DBI().open()

            log.debug("_do_copy: Releasing")
            release(lok)
            pass

        self._send(retValue)
        if self.transport is not None: self.transport.loseConnection()
        return

    def _do_release(self):
        log.debug("_do_release: has_lock => %d", self.__has_lock)
        if self.__has_lock:
            # Lock Acquire End
            DBI().task_engine.add_task(self.__id_name,
                                       dawgie.db.lockview.LockRequest.laqe)
            # Lock Release Begin
            DBI().task_engine.add_task(self.__id_name,
                                       dawgie.db.lockview.LockRequest.lrlb)

            self._unlock_db()
            self._send(True)
            # Lock Release End
            DBI().task_engine.add_task(self.__id_name,
                                       dawgie.db.lockview.LockRequest.lrle)
        else: self._send (False)
        return

    @staticmethod
    def _get_db_lock_status():
        s = dawgie.context.db_lock
        if not s:
            return Mutex.unlock
        return Mutex.lock

    def _lock_db(self):
        """Shouldn't be called directory by user"""
        dawgie.context.lock_db()
        log.debug("_lock_db: assigning lock to me.")
        self.__has_lock = True
        log.debug("_lock_db: assigning lock to me. Done.")
        return

    def _unlock_db(self):
        """Shouldn't be called directory by user"""
        log.debug("_unlock_db: unlocking...")
        dawgie.context.unlock_db()
        self.__has_lock = False
        log.debug("_unlock_db: unlocking done.")
        return
    pass

def acquire (name):
    s = dawgie.security.connect ((dawgie.context.db_host,
                                  dawgie.context.db_port))
    request = COMMAND(Func.acquire, None, None, name)
    msg = pickle.dumps (request, pickle.HIGHEST_PROTOCOL)
    s.sendall (struct.pack ('>I', len(msg)) + msg)
    buf = b''

    while buf != Mutex.unlock:
        buf = b''
        while len (buf) < 4: buf += s.recv(4 - len (buf))
        l = struct.unpack ('>I', buf)[0]
        buf = b''
        while len (buf) < l: buf += s.recv(l - len (buf))
        buf = pickle.loads(buf)
        pass
    return s

def release (s):
    request = COMMAND(Func.release, None, None, None)
    msg = pickle.dumps (request, pickle.HIGHEST_PROTOCOL)
    s.sendall (struct.pack ('>I', len(msg)) + msg)
    buf = b''
    while len (buf) < 4: buf += s.recv(4 - len (buf))
    l = struct.unpack ('>I', buf)[0]
    buf = b''
    while len (buf) < l: buf += s.recv(l - len (buf))
    s.close()
    return pickle.loads (buf)
