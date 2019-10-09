'''A coarse implementation

It does not support distribution but does support multiprocessing.
It does not support versioning.
It does not support wildcarding.

--
COPYRIGHT:
Copyright (c) 2015-2019, California Institute of Technology ("Caltech").
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

# pylint: disable=attribute-defined-outside-init,cell-var-from-loop,import-self,no-self-use,protected-access,too-many-instance-attributes,ungrouped-imports

import collections
import datetime
import enum
import dawgie
import dawgie.context
import dawgie.db.shelf
import dawgie.db.util
import dawgie.security
import dawgie.util
import dawgie.db.lockview
import glob
import logging; log = logging.getLogger(__name__)
import os
import pickle
import shelve
import struct
import twisted.internet.protocol
import twisted.internet.reactor
import twisted.internet.task
import twisted.internet.threads


COMMAND = collections.namedtuple('COMMAND', ['func', 'key', 'table', 'value'])
TABLES = collections.namedtuple('TABLES', ['alg', 'primary',
                                           'state', 'target', 'task', 'value'])

_db = None
task_engine = None
pipeline_paused = False

class Connector(object):
    # pylint: disable=too-few-public-methods
    def _acquire (self, name):
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

    def _copy (self, dst):
        return self.__do (COMMAND(Func.dbcopy, None, None, dst))

    def __do (self, request):
        s = dawgie.security.connect ((dawgie.context.db_host,
                                      dawgie.context.db_port))
        msg = pickle.dumps (request, pickle.HIGHEST_PROTOCOL)
        s.sendall (struct.pack ('>I', len(msg)) + msg)
        buf = b''
        log.info ('Connector.__do() - sending command')
        while len (buf) < 4: buf += s.recv(4 - len (buf))
        l = struct.unpack ('>I', buf)[0]
        buf = b''
        log.info ('Connector.__do() - receiving command')
        while len (buf) < l: buf += s.recv(l - len (buf))
        s.close()
        return pickle.loads (buf)

    def _get (self, key, table):
        ret = self.__do (COMMAND(Func.get, key, table, None))
        if table == Table.primary: ret = dawgie.db.util.decode (ret)
        return ret

    def _keys (self, table):
        return self.__do (COMMAND(Func.keys, None, table, None))

    def _prime_keys (self):
        log.info ('Connector._prime_keys() - get prime keys')
        return self._keys (Table.primary)

    def _release (self, s):
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

    def _set (self, key, table, value):
        if table == Table.primary: value = dawgie.db.util.encode (value)
        return self.__do (COMMAND(Func.set, key, table, value))

    def _update_cmd (self, key, table, value):
        return self.__do (COMMAND(Func.upd, key, table, value))

    def _version (self, key, table, value):
        return self.__do (COMMAND(Func.ver, key, table, value.asstring()))
    pass

class DBSerializer(twisted.internet.protocol.Factory):
    def buildProtocol (self, addr): return Worker(addr)
    pass

class Func(enum.IntEnum):
    acquire = 0
    dbcopy = 1
    get = 2
    keys = 3
    release = 4
    set = 5
    upd = 6
    ver = 7
    pass

class Interface(Connector,dawgie.Aspect,dawgie.Dataset,dawgie.Timeline):
    def __iter__(self): raise StopIteration()

    # pylint: disable=too-many-arguments
    def __to_key (self, runid, tn, taskn, algn, svn, vn):
        if not (tn.startswith ('__') and tn.endswith ('__')):
            self._update_cmd (tn, Table.target, None)
            pass

        self._update_cmd (taskn, Table.task, None)
        return dawgie.db.util.to_key (runid, tn, taskn, algn, svn, vn)

    def __verify (self, value):
        result = [False, False, False, False]
        result[0] = isinstance (value, dawgie.Value)
        # pylint: disable=bare-except
        try:
            result[1] = isinstance (value.bugfix(), int)
            result[2] = isinstance (value.design(), int)
            result[3] = isinstance (value.implementation(), int)
        except: pass
        return all (result)

    def as_dict (self) -> dict: return self.__span

    def _collect (self, refs:[(dawgie.SV_REF, dawgie.V_REF)])->None:
        self.__span = {}
        pk = {}
        tnl = self._keys (Table.target)
        for k in filter (lambda k:k[0] != '-', self._keys (Table.primary)):
            runid = int(k.split ('.')[0])
            sk = '.'.join (k.split ('.')[1:])
            pk['.'.join (k.split ('.')[1:])] = max (runid, pk.get (sk, -1))
            pass
        pk = ['.'.join ([str (i[1])] + i[0].split ('.')) for i in pk.items()]
        for ref in refs:
            clone = pickle.dumps (ref.item)
            fsvn = '.'.join ([dawgie.util.task_name (ref.factory),
                              ref.impl.name(),
                              ref.item.name()])

            if fsvn not in self.__span: self.__span[fsvn] = {}

            self.__span[fsvn].update (dict([(tn,  pickle.loads (clone))
                                            for tn in tnl]))
            for vn in ref.item.keys():
                if isinstance (ref, dawgie.V_REF) and vn != ref.feat: continue
                for k in filter (lambda k:k.endswith ('.'.join (['',fsvn,vn])),
                                 pk):
                    tn = k.split ('.')[1]
                    self.__span[fsvn][tn][vn] = self._get (k, Table.primary)
                    pass
            pass
        return

    def ds (self): return self

    def _load (self, algref=None, err=True, ver=None, lok=None):
        # pylint: disable=too-many-branches,too-many-nested-blocks,too-many-locals,too-many-statements
        if self._alg().abort(): raise dawgie.AbortAEError()

        parent= False
        if lok is None:
            name = '.'.join ([self._tn(), self._task(), self._algn()])
            parent= True
            logging.getLogger (__name__ + '.Interface').info("load: Acquiring for %s", name)
            lok = self._acquire ('load: ' + name)
            pass

        try:
            if algref:
                ft = dawgie.Factories.resolve (algref)
                tn = self._tn()

                if ft == dawgie.Factories.analysis:
                    args = (dawgie.util.task_name (algref.factory),
                            self._bot()._ps_hint(),
                            self._bot()._runid())
                    tn = '__all__'
                elif ft == dawgie.Factories.regress:
                    args = (dawgie.util.task_name (algref.factory),
                            self._bot()._ps_hint(),
                            tn)
                elif ft == dawgie.Factories.task:
                    args = (dawgie.util.task_name (algref.factory),
                            self._bot()._ps_hint(),
                            self._bot()._runid(),
                            tn)
                else:
                    raise KeyError('Unknown factory type {}'.format
                                   (algref.factory.__name__))

                child = connect (algref.impl, algref.factory (*args), tn)
                child._load (err=err, ver=ver, lok=lok)
                pass
            else:
                msv = dawgie.util.MetricStateVector(dawgie.METRIC(-1,-1,-1,-1,-1,-1),
                                                    dawgie.METRIC(-1,-1,-1,-1,-1,-1))
                for sv in self._alg().state_vectors() + [msv]:
                    base = self.__to_key (self._bot()._runid(), self._tn(),
                                          self._task(), self._algn(), sv.name(),
                                          None) + '.'

                    if not [k for k in filter (lambda n:n.startswith (base),
                                               self._keys (Table.primary))]:
                        base = self.__to_key (None, self._tn(), self._task(),
                                              self._algn(), sv.name(), None) + '.'
                        prev = -1
                        for k in self._keys (Table.primary):
                            runid = int(k.split ('.')[0])
                            if '.'.join (k.split ('.')[1:]).startswith (base):
                                prev = max (prev, runid)
                                pass
                            pass
                        pass
                    else: prev = self._bot()._runid()

                    base = self.__to_key (prev, self._tn(), self._task(),
                                          self._algn(), sv.name(), None) + '.'
                    for k in filter (lambda n:n.startswith (base),
                                     self._keys (Table.primary)):
                        sv[k.split ('.')[-1]] = self._get (k, Table.primary)
                        pass
                    pass
                self.msv = msv
                pass
        finally:
            if parent:
                logging.getLogger (__name__ + '.Interface').info("load: Releaseing for %s", name)
                self._release (lok)
                pass
            pass
        return

    def recede (self, refs:[(dawgie.SV_REF, dawgie.V_REF)])->None:
        self.__span = {}
        pk = sorted (set ([k for k in
                           filter (lambda k:k.split('.')[1] == self._tn(),
                                   self._keys (Table.primary))]))
        rids = sorted (set ([int(k.split ('.')[0]) for k in pk]))
        for ref in refs:
            clone = pickle.dumps (ref.item)
            fsvn = '.'.join ([dawgie.util.task_name (ref.factory),
                              ref.impl.name(),
                              ref.item.name()])

            if fsvn not in self.__span: self.__span[fsvn] = {}

            self.__span[fsvn].update (dict([(rid,  pickle.loads (clone))
                                            for rid in rids]))
            for vn in filter (lambda n:(not isinstance (ref,dawgie.V_REF) or
                                        n == ref.feat),
                              ref.item.keys()):
                for k in filter (lambda k:k.endswith ('.'.join (['',fsvn,vn])),
                                 pk):
                    rid = int(k.split ('.')[0])
                    self.__span[fsvn][rid][vn] = self._get (k, Table.primary)
                    pass
            pass
        return

    def _update (self):
        if self._alg().abort(): raise dawgie.AbortAEError()

        name = '.'.join ([self._tn(), self._task(), self._algn()])
        logging.getLogger (__name__ + '.Interface').info("update: Acquiring for %s", name)
        lok = self._acquire ('update: ' + name)
        valid = True
        try:
            for sv in self._alg().state_vectors():
                for k in sv.keys():
                    if not self.__verify (sv[k]):
                        logging.getLogger(__name__).critical \
                                     ('offending item is ' +
                                      '.'.join ([self._task(), self._algn(),
                                                 sv.name(), k]))
                        valid = False
                        continue
                    pass
                pass

            if not valid:
                raise dawgie.NotValidImplementationError\
                      ('StateVector contains data that does not extend ' +
                       'dawgie.Value correctly. See log for details.')

            if self._tn() not in self._keys (Table.target):\
               self._set (self._tn(), Table.target, None)

            for sv in self._alg().state_vectors():
                for k in sv.keys():
                    runid, tn, task = self._runid(), self._tn(), self._task()
                    algn, svn, vn = self._algn(), sv.name(), k
                    vname = self.__to_key (runid, tn, task, algn, svn, vn)

                    if not self._set (vname, Table.primary, sv[k]):
                        self._bot().new_values (vname)
                        pass
                    pass
                pass
        finally:
            logging.getLogger (__name__ + '.Interface').info("update: Releaseing for %s", name)
            self._release (lok)
            pass
        return

    def _update_msv (self, msv):
        if self._alg().abort(): raise dawgie.AbortAEError()

        name = '.'.join ([self._tn(), self._task(), self._algn()])
        logging.getLogger (__name__ + '.Interface').info("update: Acquiring for %s", name)
        lok = self._acquire ('update: ' + name)
        valid = True
        try:
            for k in msv.keys():
                if not self.__verify (msv[k]):
                    logging.getLogger(__name__).critical\
                        ('offending item is ' +
                         '.'.join ([self._task(), self._algn(),
                                    msv.name(), k]))
                    valid = False
                    continue
                pass

            if not valid:
                raise dawgie.NotValidImplementationError\
                      ('MetricStateVector contains data that does not extend ' +
                       'dawgie.Value correctly. See log for details.')

            if self._tn() not in self._keys (Table.target):\
               self._set (self._tn(), Table.target, None)

            for k in msv.keys():
                runid, tn, task = self._runid(), self._tn(), self._task()
                algn, svn, vn = self._algn(), msv.name(), k
                vname = self.__to_key (runid, tn, task, algn, svn, vn)

                if not self._set (vname, Table.primary, msv[k]):
                    self._bot().new_values (vname)
                    pass
                pass
        finally:
            logging.getLogger (__name__ + '.Interface').info("update: Releaseing for %s", name)
            self._release (lok)
            pass
        return
    pass

class Method(enum.Enum):
    connector = "connector"
    rsync = "rsync"
    scp = "scp"
    cp = "cp"
    pass

class Mutex(enum.Enum):
    lock = 0
    unlock = 1
    pass

class Table(enum.IntEnum):
    alg = 0
    primary = 1
    state = 2
    target = 3
    task = 4
    value = 5
    pass

class Worker(twisted.internet.protocol.Protocol):
    def __init__ (self, address):
        twisted.internet.protocol.Protocol.__init__(self)
        self.__db = dawgie.db.shelf._db
        self.__blen = len (struct.pack ('>I', 0))
        self.__buf = b''
        self.__len = None
        self.__handshake = dawgie.security.TwistedWrapper(self, address)
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
            logging.getLogger (__name__).info("ConnectionLost: Stopping looping call.")
            twisted.internet.reactor.callLater(1, self.__looping_call.stop)
            self.__looping_call_stopped = True
            pass

        if self.__has_lock:
            logging.getLogger (__name__).info("ConnectionLost: Release lock after losing connection =(")
            self._unlock_db()
            pass
        return

    def dataReceived (self, data):
        self.__buf += data
        length = self.__blen if self.__len is None else self.__len
        while length <= len (self.__buf):
            if self.__len is None:
                self.__len = struct.unpack ('>I', self.__buf[:length])[0]
                self.__buf = self.__buf[length:]
            else:
                request = pickle.loads (self.__buf[:length])
                self.__buf = self.__buf[length:]
                self.__len = None

                if request.func != Func.acquire and \
                   request.func != Func.dbcopy:
                    try: self.do (request)
                    except ImportError: logging.getLogger (__name__).excpetion ('Had a problem unpickling an input so aborting connection and moving forward.')
                    finally: self.transport.loseConnection()
                else:
                    try: self.do (request)
                    except ImportError:
                        logging.getLogger (__name__).excpetion ('Had a problem unpickling an input so aborting connection and moving forward.')
                        self.transport.loseConnection()
                        pass
                    pass
                pass

            length = self.__blen if self.__len is None else self.__len
            pass
        return

    def do (self, request):
        # pylint: disable=too-many-branches
        if request.func == Func.acquire:
            self.__id_name = request.value
            logging.getLogger (__name__).info("Inside worker(%s): Acquire",
                                              self.__id_name)
            # Lock Request Begin
            dawgie.db.shelf.task_engine.add_task(self.__id_name, dawgie.db.lockview.LockRequest.lrqb)
            self.__looping_call.start(3)
            pass
        elif request.func == Func.dbcopy:
            twisted.internet.threads.deferToThread(self._do_copy, request.value)
            pass
        elif request.func == Func.get:
            self._send (self.__db[request.table.value][request.key])
            pass
        elif request.func == Func.keys:
            log.info ('Worker.do() - received request for keys')
            log.info ('Worker.do() - table %s', request.table.name)
            log.info ('Worker.do() - table size %d', len (self.__db[request.table.value]))
            self._send ([k for k in self.__db[request.table.value].keys()])
            pass
        elif request.func == Func.release:
            logging.getLogger (__name__).info("Inside worker: Release")
            self._do_release()
            pass
        elif request.func == Func.set:
            if request.table == Table.primary:
                value,exists = dawgie.db.util.move(*request.value)
            else: value,exists = request.value,False

            self.__db[request.table.value][request.key] = value
            self._send (exists)
            pass
        elif request.func == Func.upd:
            if request.key in self.__db[request.table.value]: self._send (True)
            else:
                self.__db[request.table.value][request.key] = None
                self._send (False)
                pass
            pass
        elif request.func == Func.ver:
            dawgie.db.shelf._update (self.__db[request.table.value],
                                     request.key,
                                     request.value)
            self._send (True)
            pass
        else: logging.getLogger (__name__).error ('Did not understand ' +
                                                  str (request))
        return

    def _do_acquire(self):
        if self.__looping_call_stopped: return
        if self.__connection_lost:
            logging.getLogger (__name__).info("_do_acquire(%s): connection has already been lost", self.__id_name)
            return

        logging.getLogger(__name__).info("_do_acquire(%s): checking lock status...", self.__id_name)

        s = self._get_db_lock_status()
        if s == Mutex.unlock:
            logging.getLogger(__name__).info("_do_acquire(%s): lock is unlocked!", self.__id_name)
            self._lock_db()
            logging.getLogger(__name__).info("_do_acquire(%s): lock is now locked!", self.__id_name)
            logging.getLogger(__name__).info("_do_acquire(%s): calling stop",
                                             self.__id_name)
            twisted.internet.reactor.callLater(1, self.__looping_call.stop)
            self.__looping_call_stopped = True
            # Lock Request End
            dawgie.db.shelf.task_engine.add_task(self.__id_name, dawgie.db.lockview.LockRequest.lrqe)

            # Lock Acquire Begin
            dawgie.db.shelf.task_engine.add_task(self.__id_name, dawgie.db.lockview.LockRequest.laqb)
            pass
        self._send(s)
        return

    def _do_copy(self, param):
        method = param[0]
        dst = param[1]
        src = dawgie.context.db_path
        tmpdst = dawgie.db.shelf.mkStgDir()
        retValue = None

        logging.getLogger (__name__).info("_do_copy: Acquiring. dst -> %s", dst)
        connection = Interface(None, None, None)
        lok = connection._acquire('copy')

        try:
            logging.getLogger (__name__).info("_do_copy: Got lok")
            src = dawgie.context.db_path

            if os.path.exists(src):
                dawgie.db.shelf.close()
                if method == Method.connector:
                    dawgie.db.shelf.open_db()
                    retValue = {}
                    for i in dawgie.db.shelf._db._fields:
                        retValue[i] = dict(getattr(dawgie.db.shelf._db, i))
                        pass
                    pass
                else:
                    r = os.system("rsync --delete -ax %s/ %s/" % (src, tmpdst))
                    retValue = tmpdst if r == 0 else None
                    dawgie.db.shelf.open_db()
                    pass
            else:
                logging.getLogger (__name__).error ('%s does not exists.', src)
                retValue = None
        finally:
            if dawgie.db.shelf._db is None:
                dawgie.db.shelf.open_db()

            logging.getLogger (__name__).info("_do_copy: Releasing")
            connection. _release(lok)
            pass

        self._send(retValue)
        self.transport.loseConnection()
        return

    def _do_release(self):
        logging.getLogger (__name__).info("_do_release: has_lock => %d",
                                          self.__has_lock)
        if self.__has_lock:
            # Lock Acquire End
            dawgie.db.shelf.task_engine.add_task(self.__id_name, dawgie.db.lockview.LockRequest.laqe)
            # Lock Release Begin
            dawgie.db.shelf.task_engine.add_task(self.__id_name, dawgie.db.lockview.LockRequest.lrlb)

            self._unlock_db()
            self._send(True)
            # Lock Release End
            dawgie.db.shelf.task_engine.add_task(self.__id_name, dawgie.db.lockview.LockRequest.lrle)
            pass
        else: self._send (False)
        return

    def _get_db_lock_status(self):
        s = dawgie.context.db_lock
        if not s:
            return Mutex.unlock
        return Mutex.lock

    def _lock_db(self):
        """Shouldn't be called directory by user"""
        dawgie.context.lock_db()
        logging.getLogger (__name__).info("_lock_db: assigning lock to me.")
        self.__has_lock = True
        logging.getLogger (__name__).info("_lock_db: assigning lock to me. Done.")
        return

    def _unlock_db(self):
        """Shouldn't be called directory by user"""
        logging.getLogger (__name__).info("_unlock_db: unlocking...")
        dawgie.context.unlock_db()
        self.__has_lock = False
        logging.getLogger (__name__).info("_unlock_db: unlocking done.")
        return

    pass

def _connect():
    return Connector()

def _copy (table):
    return dict([(k,table[k]) for k in table.keys()])

def _prime_keys():
    log.info ('_prime_keys() - size is %d', len (dawgie.db.shelf._db.primary))
    return dawgie.db.shelf._db.primary.keys()
def _prime_values():
    return dawgie.db.shelf._db.primary.values()
def _update (table, name, ver):
    if name not in table: table[name] = []
    if table[name].count (str (ver)) == 0:
        l = table[name]
        l.append (str (ver))
        table[name] = l
        pass
    return

def archive (done):
    path = dawgie.context.db_rotate_path
    if not (os.path.exists (path) and os.path.isdir (path)):
        raise ValueError('The path "' + path +
                         '" does not exist or is not a directory')

    if dawgie.db.shelf._db is not None:
        reconnect = True
        logging.getLogger(__name__).critical ('called _rotate after open')
        dawgie.db.shelf.close()
    else: reconnect = False

    orig = dawgie.db.shelf.rotated_files()
    backup = {}

    for i in range(dawgie.context.db_rotate):
        backup[i] = dawgie.db.shelf.rotated_files(i)

    dawgie.db.util.rotate(path, orig, backup)

    overflowNum = len(backup)
    orig = dawgie.db.shelf.rotated_files(overflowNum)
    for e in orig: os.remove(e)

    if reconnect: dawgie.db.shelf.open_db()

    done()
    return

def close():
    if dawgie.db.shelf._db is not None:
        if isinstance(dawgie.db.shelf._db, bool): dawgie.db.shelf._db = None
        if isinstance(dawgie.db.shelf._db, TABLES):
            dawgie.db.shelf._db.alg.close()
            dawgie.db.shelf._db.primary.close()
            dawgie.db.shelf._db.state.close()
            dawgie.db.shelf._db.target.close()
            dawgie.db.shelf._db.task.close()
            dawgie.db.shelf._db.value.close()
            dawgie.db.shelf._db = None
            pass
        pass
    return

def connect (alg, bot, tn):
    if dawgie.db.shelf._db is None:
        raise RuntimeError('called connect before open')
    return Interface(alg, bot, tn)

def copy(dst, method=Method.connector, gateway=dawgie.context.db_host):
    if dawgie.db.shelf._db is None:
        raise RuntimeError('called copy before open')

    connection = Connector()
    retValue = connection._copy([method,dst])

    if method == Method.connector:
        db = retValue
        path = os.path.join (dst, dawgie.context.db_name)
        newDb = dawgie.db.shelf.open_shelve(path)
        newDb.alg.update(db['alg'])
        newDb.primary.update(db['primary'])
        newDb.state.update(db['state'])
        newDb.target.update(db['target'])
        newDb.task.update(db['task'])
        newDb.value.update(db['value'])

        newDb.alg.close()
        newDb.primary.close()
        newDb.state.close()
        newDb.target.close()
        newDb.task.close()
        newDb.value.close()

        status = 0
    elif method == Method.rsync:
        tmpdir = retValue
        status = os.system("rsync --delete -ax %s:%s/ %s/" % (gateway, tmpdir, dst))
    elif method == Method.scp:
        tmpdir = retValue
        status = os.system("scp -rp %s:%s/* %s/" % (gateway, tmpdir, dst))
    elif method == Method.cp:
        tmpdir = retValue
        status = os.system("cp -rp %s/* %s/" % (tmpdir, dst))

    return status

def gather (anz, ans):
    if dawgie.db.shelf._db is None:
        raise RuntimeError('called connect before open')
    return Interface(anz, ans, '__all__')

def metrics()->'[dawgie.db.METRIC_DATA]':
    if dawgie.db.shelf._db is None:
        raise RuntimeError('called metrics before open')

    result = []
    log.info ('metrics() - starting')
    keys = [k for k in _prime_keys()]
    log.info ('metrics() - total prime keys %d', len (keys))
    keys = [k for k in sorted (filter (lambda s:s.split('.')[4] == '__metric__', keys))]
    log.info ('metrics() - total __metric__ in prime keys %d', len (keys))
    for m in keys:
        log.info ('metrics() - working on %s', m)
        runid,target,task,algn,_svn,vn = m.split('.')

        if not result or any ([result[-1].run_id != runid,
                               result[-1].target != target,
                               result[-1].task != task,
                               result[-1].alg_name != algn]):
            log.info ('metrics() - make new reuslt')
            msv = dawgie.util.MetricStateVector(dawgie.METRIC(-2,-2,-2,-2,-2,-2),
                                                dawgie.METRIC(-2,-2,-2,-2,-2,-2))
            result.append (dawgie.db.METRIC_DATA(alg_name=algn,
                                                 alg_ver=dawgie.VERSION(-1,-1,-1),
                                                 run_id=runid, sv=msv,
                                                 target=target, task=task))
            log.info ('metrics() - result length %d', len (result))
            pass

        try:
            log.info ('metrics() - reading data and decoding')
            msv[vn] = dawgie.db.util.decode (dawgie.db.shelf._db.primary[m])
        except FileNotFoundError: log.exception('missing metric data for %s',m)
        pass
    return result

def mkStgDir():
    t = datetime.datetime.now()
    tString = "%s/%d%d%d%d%d%d%d" % (dawgie.context.data_stg, t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond)
    os.system("mkdir %s" % tString)
    return tString

# pylint: disable=redefined-builtin
def next():
    if dawgie.db.shelf._db is None:
        raise RuntimeError('called next before open')

    if not dawgie.db.shelf._db.primary.keys(): runid = 1
    else: runid = max([int(k.split('.')[0])
                       for k in dawgie.db.shelf._db.primary.keys()]) + 1

    return runid

# pylint: disable=redefined-builtin
def open():
    dawgie.db.shelf.open_db()
    try: twisted.internet.reactor.listenTCP(int(dawgie.context.db_port),
                                            DBSerializer(),
                                            dawgie.context.worker_backlog)
    except twisted.internet.error.CannotListenError:\
        logging.getLogger(__name__).warning("Address  already in use.")
    return

def open_db():
    if not (os.path.exists (dawgie.context.db_path) and
            os.path.isdir (dawgie.context.db_path)):
        raise ValueError('The path "' + dawgie.context.db_path +
                         '" does not exist or is not a directory')

    if dawgie.db.shelf.task_engine is None:
        dawgie.db.shelf.task_engine = dawgie.db.lockview.TaskLockEngine()
    if dawgie.db.shelf._db is None:
        path = os.path.join (dawgie.context.db_path,
                             dawgie.context.db_name)
        dawgie.db.shelf._db = dawgie.db.shelf.open_shelve(path)

    return

def open_shelve(path):
    return TABLES(alg=shelve.open (path + '.alg'),
                  primary=shelve.open (path + '.prime'),
                  state=shelve.open (path + '.state'),
                  target=shelve.open (path + '.target'),
                  task=shelve.open (path + '.task'),
                  value=shelve.open (path + '.value'))

# pylint: disable=too-many-arguments
def remove (runid, tn, taskn, algn, svn, vn):
    k = dawgie.db.util.to_key (runid, tn, taskn, algn, svn, vn)

    if k in dawgie.db.shelf._db.primary:
        v = dawgie.db.shelf._db.primary[k]
        del dawgie.db.shelf._db.primary[k]
        logging.getLogger (__name__).warning ('removed (' + k + ', ' + v + ')')
        pass
    else: logging.getLogger (__name__).error ('remove() could not find the key "' + k + '" in the primary table. Ignoring request.')
    return

def reopen():
    if dawgie.db.shelf._db is None: dawgie.db.shelf._db = True
    return

def reset (runid:int, tn:str, tskn, alg)->None:
    # pylint: disable=unused-argument
    return

def rotated_files(index=None):
    path = dawgie.context.db_rotate_path
    if index is None:
        orig = glob.glob("%s/sdp.alg" % path)
        orig += glob.glob("%s/sdp.prime" % path)
        orig += glob.glob("%s/sdp.state" % path)
        orig += glob.glob("%s/sdp.target" % path)
        orig += glob.glob("%s/sdp.task" % path)
        orig += glob.glob("%s/sdp.value" % path)
        return orig
    orig = glob.glob("%s/%d.sdp.alg" % (path, index))
    orig += glob.glob("%s/%d.sdp.prime" % (path, index))
    orig += glob.glob("%s/%d.sdp.state" % (path, index))
    orig += glob.glob("%s/%d.sdp.target" % (path, index))
    orig += glob.glob("%s/%d.sdp.task" % (path, index))
    orig += glob.glob("%s/%d.sdp.value" % (path, index))
    return orig

def retreat (reg, ret):
    if dawgie.db.shelf._db is None:
        raise RuntimeError('called connect before open')
    return Interface(reg, ret, ret._target)

def targets():
    if isinstance (dawgie.db.shelf._db, bool): result = Connector()._keys (Table.target)
    else: result = [k for k in dawgie.db.shelf._db.target.keys()]
    return result

def trace (task_alg_names):
    result = {}
    for tn in dawgie.db.targets():
        result[tn] = {}
        for tan in task_alg_names: result[tn][tan] = None
        pass
    return result

def update (tsk, alg, sv, vn, v):
    if dawgie.db.shelf._db is None:
        raise RuntimeError('called next before open')

    connection = Connector()
    connection._update_cmd (tsk._name(), Table.task, None)
    connection._version ('.'.join ([tsk._name(), alg.name()]), Table.alg, alg)

    if sv:
        connection._version ('.'.join ([tsk._name(), alg.name(), sv.name()]),
                             Table.state, sv)
        connection._version ('.'.join ([tsk._name(), alg.name(), sv.name(),vn]),
                             Table.value, v)
        pass
    return

def versions():
    if dawgie.db.shelf._db is None:
        raise RuntimeError('called next before open')

    alg = _copy (dawgie.db.shelf._db.alg)
    sv = _copy (dawgie.db.shelf._db.state)
    t = _copy (dawgie.db.shelf._db.task)
    v = _copy (dawgie.db.shelf._db.value)
    return t,alg,sv,v

def view_locks(): return dawgie.db.shelf.task_engine.view_progress()
