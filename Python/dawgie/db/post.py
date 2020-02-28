'''Postgresql implementation

--
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

# pylint: disable=import-self,protected-access

import collections
import dawgie
import dawgie.context
import dawgie.db
import dawgie.db.post
import dawgie.db.util
import dawgie.db.util.aspect
import dawgie.util
import logging; log = logging.getLogger(__name__)
import os
import pickle
import psycopg2
import psycopg2.extras
import shutil
import twisted.internet.error
import twisted.internet.protocol
import twisted.internet.reactor

_db = None

ENTRY = collections.namedtuple('ENTRY',['run_ID', 'tn_ID', 'task_ID',
                                        'alg_ID', 'sv_ID', 'val_ID'])

class ArchiveHandler(twisted.internet.protocol.ProcessProtocol):
    def __init__ (self, command, done):
        self.__command = command
        self.__done = done
        return

    def processEnded(self, reason):
        if isinstance (reason.value, twisted.internet.error.ProcessTerminated):
            log.critical ('Error in archiving of data.    EXIT CODE: %s' +
                          '   SIGNAL: %s    STATUS: %s   COMMAND: "%s"',
                          str (reason.value.exitCode),
                          str (reason.value.signal),
                          str (reason.value.status),
                          self.__command)
            pass

        self.__done()
        return
    pass

class Interface(dawgie.db.util.aspect.Container,dawgie.Dataset,dawgie.Timeline):
    def __init__(self, *args):
        dawgie.db.util.aspect.Container.__init__(self)
        dawgie.Dataset.__init__(self, *args)
        self.__span = {}
        return

    # pylint: disable=too-many-arguments
    @staticmethod
    def __fill (cur, sv, alg_ID, run_ID, task_ID, tn_ID, sv_ID):
        # Get rows from primary table that have these algorithm primary keys
        cur.execute('SELECT val_ID,blob_name from Prime WHERE run_ID = %s ' +
                    'and alg_ID = %s and tn_ID = %s ' +
                    'and task_ID = %s and sv_ID = %s;',
                    (run_ID, alg_ID, tn_ID, task_ID, sv_ID))
        runs = cur.fetchall()

        if not runs: log.info ('Dataset load: Could not find any ' +
                               'runs that match given values')

        for r in runs:
            val_ID = r[0]
            cur.execute('SELECT name from Value WHERE PK = %s;', [val_ID])
            val_name = cur.fetchone()[0]
            data_valPickle = r[1]
            sv[val_name] = dawgie.db.util.decode(data_valPickle)
            pass
        return
    # pylint: enable=too-many-arguments

    def __purge (self):
        table = self.__span['table']
        for k1 in [k for k in table]:
            for k2 in [k for k in table[k1]]:
                if not table[k1][2]:
                    log.warning ('No data found for keys [%s][%s]',
                                 str(k1), str(k2))
                    del table[k1][k2]
                pass

            if not table[k1]:
                log.warning ('No data found for key %s ', str(k1))
                del table[k1]
                pass
            pass
        return

    def __tn_id (self, conn, cur):
        # Get target id that matches target name or create it if not there
        try:
            cur.execute('INSERT into Target (name) values (%s)', [self._tn()])
            conn.commit()
        except psycopg2.IntegrityError: conn.rollback()
        except psycopg2.ProgrammingError: conn.rollback()  # permission issue
        cur.execute('SELECT * from Target WHERE name = %s;',
                    [self._tn()])
        tn_ID = _fetchone(cur,'Dataset: Could not find target ID')
        return tn_ID

    @staticmethod
    def __verify (value):
        # pylint: disable=bare-except
        result = [False, False, False, False]
        result[0] = isinstance (value, dawgie.Value)
        try:
            result[1] = isinstance (value.bugfix(), int)
            result[2] = isinstance (value.design(), int)
            result[3] = isinstance (value.implementation(), int)
        except: pass
        return all (result)

    def _ckeys (self, l1k, l2k):
        if l2k: keys = self.__span['table'][l1k][l2k].keys()
        elif l1k: keys = self.__span['table'][l1k].keys()
        else: keys = self.__span['table'].keys()
        return keys

    def _collect (self, refs:[(dawgie.SV_REF, dawgie.V_REF)])->None:
        # pylint: disable=too-many-locals
        conn = dawgie.db.post._conn()
        cur = dawgie.db.post._cur (conn)
        self.__span = {'sv_templates':
                       dict([('.'.join ([dawgie.util.task_name (ref.factory),
                                         ref.impl.name(),
                                         ref.item.name()]),
                              pickle.dumps (ref.item)) for ref in refs]),
                       'table':{}}
        cur.execute ('SELECT PK,name from Target;')
        tnl = cur.fetchall()
        for ref in refs:
            cur.execute ('SELECT PK FROM Task WHERE name = %s;',
                         [dawgie.util.task_name (ref.factory)])
            task_ID = cur.fetchone()[0]
            cur.execute('SELECT PK from Algorithm WHERE name = %s and ' +
                        'task_ID = %s and ' +
                        'design = %s and implementation = %s and bugfix = %s;',
                        (ref.impl.name(), task_ID, ref.impl.design(),
                         ref.impl.implementation(), ref.impl.bugfix()))
            alg_ID = cur.fetchone()[0]
            cur.execute('SELECT PK FROM StateVector WHERE name = %s and ' +
                        'alg_ID = %s and ' +
                        'design = %s and implementation = %s and bugfix = %s;',
                        (ref.item.name(), alg_ID, ref.item.design(),
                         ref.item.implementation(), ref.item.bugfix()))
            sv_ID = cur.fetchone()[0]
            fsvn = '.'.join ([dawgie.util.task_name (ref.factory),
                              ref.impl.name(),
                              ref.item.name()])
            for tn in tnl:
                cur.execute('SELECT run_ID FROM Prime WHERE tn_ID = %s AND ' +
                            'task_ID = %s AND alg_ID = %s AND sv_ID = %s;',
                            [tn[0], task_ID, alg_ID, sv_ID])
                run_ID = set([rid[0] for rid in cur.fetchall()])

                if not run_ID:
                    log.warning ('Aspect collect: Could not find any ' +
                                 'runids for ' + str (ref))
                    continue

                run_ID = max (run_ID) if 1 < len (run_ID) else run_ID.pop()
                cur.execute('SELECT val_ID from Prime WHERE run_ID = %s AND ' +
                            'alg_ID = %s AND tn_ID = %s and task_ID = %s and ' +
                            'sv_ID = %s;',
                            (run_ID, alg_ID, tn[0], task_ID, sv_ID))
                vids = [vid[0] for vid in cur.fetchall()]

                if not vids:
                    log.warning ('Aspect collect: Could not find any ' +
                                 'values for ' + str (ref))
                elif tn[1] not in self.__span['table']:
                    self.__span['table'][tn[1]] = {}
                    pass

                for vid in vids:
                    cur.execute ('SELECT name FROM Value WHERE pk = %s;', [vid])
                    vn = cur.fetchone()[0]
                    entry = ENTRY(run_ID, tn[0], task_ID, alg_ID, sv_ID, vid)

                    if fsvn not in self.__span['table'][tn[1]]:\
                       self.__span['table'][tn[1]][fsvn] = {}

                    if isinstance (ref, dawgie.SV_REF):
                        self.__span['table'][tn[1]][fsvn][vn] = entry
                    elif isinstance (ref, dawgie.V_REF):
                        if ref.feat == vn:
                            self.__span['table'][tn[1]][fsvn][vn] = entry
                            pass
                        pass
                    else: log.critical ('Need to improve compliant because ' +
                                        'received soemthing that was neither ' +
                                        'SV_REF or V_REF: ' + str (type (ref)))
                    pass
                pass
            pass
        conn.commit()
        cur.close()
        conn.close()
        self.__purge()
        return

    def _fill_item (self, l1k, l2k, l3k):
        if isinstance (self.__span['table'][l1k][l2k][l3k], ENTRY):
            conn = dawgie.db.post._conn()
            cur = dawgie.db.post._cur (conn)
            cur.execute ('SELECT blob_name from Prime WHERE run_ID = %s and ' +
                         'tn_ID = %s and task_ID = %s and alg_ID = %s and ' +
                         'sv_ID = %s and val_ID = %s;',
                         self.__span['table'][l1k][l2k][l3k])
            value = dawgie.db.util.decode (*cur.fetchone())
            cur.execute ('SELECT design,implementation,bugfix ' +
                         'FROM StateVector WHERE pk= %s;',
                         [self.__span['table'][l1k][l2k][l3k].sv_ID])
            value._set_ver (dawgie.VERSION(*cur.fetchone()))
            self.__span['table'][l1k][l2k][l3k] = value
            conn.commit()
            cur.close()
            conn.close()
        else: value = self.__span['table'][l1k][l2k][l3k]
        return value

    def _load (self, algref=None, err=True, ver=None):
        # Load state vectors with data from db into algorithm
        # Take highest run number row from primary table for that task,
        #   algorithm, state vector if current run does not exist in
        #   Primary table.
        # pylint: disable=too-many-locals,too-many-statements
        if self._alg().abort(): raise dawgie.AbortAEError()

        log.info ("In Interface load")
        conn = dawgie.db.post._conn()
        cur = dawgie.db.post._cur (conn)

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
                        self._tn())
            elif ft == dawgie.Factories.task:
                args = (dawgie.util.task_name (algref.factory),
                        self._bot()._ps_hint(),
                        self._bot()._runid(),
                        self._tn())
            else:
                raise KeyError('Unknown factory type {}'.format
                               (algref.factory.__name__))

            child = connect (algref.impl, algref.factory (*args), tn)
            child.load(err=err, ver=ver)
        else:
            # get the target
            tn_ID = self.__tn_id (conn, cur)
            # Get task id that matches task name
            cur.execute('SELECT * from TASK WHERE name = %s;',
                        [self._task()])
            task_ID = _fetchone (cur, 'Dataset load: Could not find task ID')
            cur.execute('SELECT pk FROM Algorithm WHERE name = %s AND ' +
                        'task_ID = %s;', [self._alg().name(), task_ID])
            alg_ID = list(set([pk[0] for pk in cur.fetchall()]))
            msv = dawgie.util.MetricStateVector(dawgie.METRIC(-1,-1,-1,-1,-1,-1),
                                                dawgie.METRIC(-1,-1,-1,-1,-1,-1))
            for sv in self._alg().state_vectors() + [msv]:
                cur.execute('SELECT pk FROM StateVector WHERE name = %s AND ' +
                            'alg_ID = ANY(%s);', [sv.name(), alg_ID])
                sv_ID = list(set([pk[0] for pk in cur.fetchall()]))
                cur.execute('SELECT run_ID FROM Prime WHERE tn_ID = %s AND ' +
                            'task_ID = %s AND alg_ID = ANY(%s) AND '+
                            'sv_ID = ANY(%s);',
                            [tn_ID, task_ID, alg_ID, sv_ID])
                run_ID = set([pk[0] for pk in cur.fetchall()])

                if not run_ID:
                    log.info ('Dataset load: Could not find any runs that ' +
                              'match given the algorithm and state vector')
                    continue
                else:
                    run_ID = self._runid() if self._runid() in run_ID \
                                           else max(run_ID)
                    cur.execute ('SELECT alg_ID,sv_ID FROM Prime WHERE ' +
                                 'run_ID = %s AND tn_ID = %s AND task_ID = %s '+
                                 ' AND alg_ID = ANY(%s) and sv_ID = ANY(%s);',
                                 [run_ID, tn_ID, task_ID, alg_ID, sv_ID])
                    narrowed = set(cur.fetchall())

                if len (narrowed) != 1:
                    log.critical ('Dataset load: The postgres db is corrupt '+
                                  'because found %d IDs', len (narrowed))
                    pass

                na_ID,nsv_ID = narrowed.pop()
                self.__fill (cur, sv, na_ID, run_ID, task_ID, tn_ID, nsv_ID)
                cur.execute ('SELECT design,implementation,bugfix ' +
                             'FROM Algorithm WHERE pk = %s;', [na_ID])
                av = cur.fetchone()
                cur.execute ('SELECT design,implementation,bugfix ' +
                             'FROM StateVector WHERE pk= %s;', [nsv_ID])
                svv = cur.fetchone()
                self._alg()._version_seal_ = dawgie.VERSION(*av)
                sv._version_seal_ = dawgie.VERSION(*svv)
                pass
            self.msv = msv
            pass

        conn.commit()
        cur.close()
        conn.close()
        return

    def ds(self): return self

    def recede (self, refs:[(dawgie.SV_REF, dawgie.V_REF)])->None:
        # pylint: disable=too-many-locals,too-many-statements
        conn = dawgie.db.post._conn()
        cur = dawgie.db.post._cur (conn)
        self.__span = {'sv_templates':
                       dict([('.'.join ([dawgie.util.task_name (ref.factory),
                                         ref.impl.name(),
                                         ref.item.name()]),
                              pickle.dumps (ref.item)) for ref in refs]),
                       'table':{}}
        cur.execute ('SELECT PK FROM Target WHERE name = %s;', [self._tn()])
        tnid = cur.fetchone()[0]
        for ref in refs:
            cur.execute ('SELECT PK FROM Task WHERE name = %s;',
                         [dawgie.util.task_name (ref.factory)])
            task_ID = cur.fetchone()[0]
            cur.execute('SELECT PK from Algorithm WHERE name = %s and ' +
                        'task_ID = %s;',
                        (ref.impl.name(), task_ID,))
            alg_IDs = cur.fetchall()
            cur.execute('SELECT PK FROM StateVector WHERE name = %s and ' +
                        'alg_ID = ANY(%s);',
                        (ref.item.name(), alg_IDs,))
            sv_IDs = cur.fetchall()
            fsvn = '.'.join ([dawgie.util.task_name (ref.factory),
                              ref.impl.name(),
                              ref.item.name()])
            cur.execute ('SELECT run_ID FROM Prime WHERE tn_ID = %s AND ' +
                         'task_ID = %s AND alg_ID = ANY(%s) AND ' +
                         'sv_ID = ANY(%s);', [tnid, task_ID, alg_IDs, sv_IDs])
            rids = sorted (set ([r[0] for r in cur.fetchall()]))
            for rid in rids:
                cur.execute ('SELECT alg_ID,sv_ID FROM Prime WHERE ' +
                             'run_ID = %s AND  tn_ID = %s AND ' +
                             'task_ID = %s AND alg_ID = ANY(%s) AND ' +
                             'sv_ID = ANY(%s);',
                             [rid, tnid, task_ID, alg_IDs, sv_IDs])
                ids = cur.fetchall()
                aids = set ([id[0] for id in ids])
                svids = set ([id[1] for id in ids])

                if len (aids) != 1 and len (svids) != 1:
                    log.critical ('Database corruption from many versions ' +
                                  'at one run id.')
                    continue
                else: alg_ID,sv_ID = aids.pop(),svids.pop()

                cur.execute('SELECT val_ID from Prime WHERE run_ID = %s AND ' +
                            'alg_ID = %s AND tn_ID = %s and task_ID = %s and ' +
                            'sv_ID = %s;',
                            (rid, alg_ID, tnid, task_ID, sv_ID))
                vids = [vid[0] for vid in cur.fetchall()]

                if not vids:
                    log.warning ('Regress recede: Could not find any ' +
                                 'values for ' + str (ref))
                elif rid not in self.__span['table']:
                    self.__span['table'][rid] = {}
                    pass

                for vid in vids:
                    cur.execute ('SELECT name FROM Value WHERE pk = %s;', [vid])
                    vn = cur.fetchone()[0]
                    entry = ENTRY(rid, tnid, task_ID, alg_ID, sv_ID, vid)

                    if fsvn not in self.__span['table'][rid]:\
                       self.__span['table'][rid][fsvn] = {}

                    if isinstance (ref, dawgie.SV_REF):
                        self.__span['table'][rid][fsvn][vn] = entry
                    elif isinstance (ref, dawgie.V_REF):
                        if ref.feat == vn:
                            self.__span['table'][rid][fsvn][vn] = entry
                            pass
                        pass
                    else: log.critical ('Need to improve compliant because ' +
                                        'received soemthing that was neither ' +
                                        'SV_REF or V_REF: ' + str (type (ref)))
                    pass
                pass
            pass
        conn.commit()
        cur.close()
        conn.close()
        self.__purge()
        return

    def _update (self):
        # pylint: disable=too-many-locals,too-many-statements
        if self._alg().abort(): raise dawgie.AbortAEError()

        log.info ("in Interface update")
        conn = dawgie.db.post._conn()
        cur = dawgie.db.post._cur (conn)
        primes = []
        valid = True
        for sv in self._alg().state_vectors():
            for vn,val in sv.items():
                result, exists = dawgie.db.util.move\
                                 (*dawgie.db.util.encode (val))
                cur.execute('SELECT EXISTS (SELECT * from Prime where ' +
                            'blob_name = %s);', [result])
                exists &= cur.fetchone()[0]

                if not exists:
                    self._bot().new_values ('.'.join ([str (self._runid()),
                                                       self._tn(),
                                                       self._task(),
                                                       self._alg().name(),
                                                       sv.name(), vn]))
                    pass

                # Put result in primary. Make sure to get task_ID and other
                # primary keys from their respective tables

                # get the target ID
                tn_ID = self.__tn_id (conn, cur)

                # Get task id that matches task name
                cur.execute('SELECT * from TASK WHERE name = %s;',
                            [self._task()])
                task_ID = _fetchone(cur,
                                    'Dataset update: Could not find task ID')

                # Get Alg id
                cur.execute('SELECT * from Algorithm WHERE name = %s and ' +
                            'task_ID = %s and ' +
                            'design = %s and bugfix = %s and implementation = %s;',
                            (self._alg().name(), task_ID, self._alg().design(),
                             self._alg().bugfix(), self._alg().implementation()))
                alg_ID = _fetchone(cur,
                                   'Dataset update: Could not find ' +
                                   'algorithm ID')

                # Get state vector id that matches sv name
                cur.execute('SELECT * from StateVector WHERE name = %s and ' +
                            'alg_ID = %s and ' +
                            'design = %s and bugfix = %s and implementation = %s;',
                            [sv.name(), alg_ID, sv.design(), sv.bugfix(),
                             sv.implementation()])
                sv_ID = _fetchone(cur, 'Dataset load: Could not find ' +
                                  'state vector ID')

                # Get the value id that matches the value
                if not self.__verify (val):
                    log.critical ('offending item is ' +
                                  '.'.join ([self._task(), self._alg().name(),
                                             sv.name(), vn]))
                    valid = False
                    continue

                args = ('SELECT * from value where name = %s and ' +
                        'sv_ID = %s and ' +
                        'design = %s and bugfix = %s and implementation = %s;',
                        (vn, sv_ID, val.design(), val.bugfix(),
                         val.implementation()))
                cur.execute (*args)
                val_ID = cur.fetchone()
                if val_ID is None:
                    try:
                        cur.execute('INSERT into Value (name, sv_id, design, '+
                                    'bugfix, implementation) values ' +
                                    '(%s, %s, %s, %s, %s);',
                                    (vn, sv_ID, val.design(), val.bugfix(),
                                     val.implementation()))
                        conn.commit()
                    except psycopg2.IntegrityError: conn.rollback()
                    cur.execute (*args)
                    val_ID = cur.fetchone()
                    pass
                primes.append (('INSERT into Prime (run_ID, task_ID, tn_ID, ' +
                                'alg_ID, sv_ID, val_ID, blob_name) values ' +
                                '(%s, %s, %s, %s, %s, %s, %s);',
                                (self._runid(), task_ID, tn_ID, alg_ID, sv_ID,
                                 val_ID[0], result)))
                pass
            pass

        if not valid:
            raise dawgie.NotValidImplementationError\
                  ('StateVector contains data that does not extend ' +
                   'dawgie.Value correctly. See log for details.')

        while primes:
            cur = dawgie.db.post._cur (conn)
            try:
                for args in primes: cur.execute (*args)
                conn.commit()
                primes.clear()
            except psycopg2.IntegrityError: conn.rollback()
            pass
        cur.close()
        conn.close()
        return

    def _update_msv (self, msv):
        # pylint: disable=too-many-locals,too-many-statements
        if self._alg().abort(): raise dawgie.AbortAEError()

        log.info ("in Interface update process metrics")
        conn = dawgie.db.post._conn()
        cur = dawgie.db.post._cur (conn)
        primes = []
        valid = True
        for vn,val in msv.items():
            result = dawgie.db.util.move (*dawgie.db.util.encode (val))[0]
            # Put result in primary. Make sure to get task_ID and other
            # primary keys from their respective tables

            # get the target ID
            tn_ID = self.__tn_id (conn, cur)

            # Get task id that matches task name
            cur.execute('SELECT * from TASK WHERE name = %s;', [self._task()])
            task_ID = _fetchone (cur, 'Dataset update: Could not find task ID')

            # Get Alg id
            cur.execute('SELECT * from Algorithm WHERE name = %s and ' +
                        'task_ID = %s and ' +
                        'design = %s and bugfix = %s and implementation = %s;',
                        (self._alg().name(), task_ID, self._alg().design(),
                         self._alg().bugfix(), self._alg().implementation()))
            alg_ID = _fetchone (cur, 'Dataset update: Could not find ' +
                                'algorithm ID')

            # Get state vector id that matches msv name
            args = ('SELECT * from StateVector WHERE name = %s and ' +
                    'alg_ID = %s and ' +
                    'design = %s and bugfix = %s and implementation = %s;',
                    (msv.name(), alg_ID, msv.design(), msv.bugfix(),
                     msv.implementation()))
            cur.execute (*args)
            sv_ID = cur.fetchone()

            if sv_ID is None:
                try:
                    cur.execute ('INSERT into StateVector ' +
                                 '(name, alg_ID, design, bugfix, ' +
                                 'implementation) values (%s, %s, %s, %s, %s);',
                                 (msv.name(),alg_ID,msv.design(),msv.bugfix(),
                                  msv.implementation()))
                    conn.commit()
                except psycopg2.IntegrityError: conn.rollback()
                cur.execute (*args)
                sv_ID = cur.fetchone()
                pass

            # Get the value id that matches the value
            if not self.__verify (val):
                log.critical ('offending item is ' +
                              '.'.join ([self._task(), self._alg().name(),
                                         msv.name(), vn]))
                valid = False
                continue

            args = ('SELECT * from Value where name = %s and ' +
                    'sv_ID = %s and ' +
                    'design = %s and bugfix = %s and implementation = %s;',
                    (vn, sv_ID[0], val.design(), val.bugfix(),
                     val.implementation()))
            cur.execute (*args)
            val_ID = cur.fetchone()

            if val_ID is None:
                try:
                    cur.execute('INSERT into Value (name, sv_id, design, '+
                                'bugfix, implementation) values ' +
                                '(%s, %s, %s, %s, %s);',
                                (vn, sv_ID[0], val.design(), val.bugfix(),
                                 val.implementation()))
                    conn.commit()
                except psycopg2.IntegrityError: conn.rollback()
                cur.execute (*args)
                val_ID = cur.fetchone()
                pass
            primes.append (('INSERT into Prime (run_ID, task_ID, tn_ID, ' +
                            'alg_ID, sv_ID, val_ID, blob_name) values ' +
                            '(%s, %s, %s, %s, %s, %s, %s);',
                            (self._runid(), task_ID, tn_ID, alg_ID, sv_ID[0],
                             val_ID[0], result)))
            pass

        if not valid:
            raise dawgie.NotValidImplementationError\
                  ('MetricStateVector contains data that does not extend ' +
                   'dawgie.Value correctly. See log for details.')

        while primes:
            cur = dawgie.db.post._cur (conn)
            try:
                for args in primes: cur.execute (*args)
                conn.commit()
                primes.clear()
            except psycopg2.IntegrityError: conn.rollback()
            pass
        cur.close()
        conn.close()
        return
    pass

class MyVersion(dawgie.Version):
    # Version takes int design, implementation, and bugfix
    # Conglomerates above information into one object per version
    # Used with StateVector, Value, and Algorithm
    def __init__ (self, design, impl, bf):
        dawgie.Version.__init__ (self)
        self._version_ = dawgie.VERSION(design, impl, bf)
        return
    pass

def _append_ver (d:dict, k:str, v:str):
    if k not in d: d[k] = []
    d[k].append (v)
    return

def _conn():
    log.info ('using db_path %s', dawgie.context.db_path)
    return psycopg2.connect(database=dawgie.context.db_name,
                            host=dawgie.context.db_host,
                            password=dawgie.context.db_path.split(':')[1],
                            port=dawgie.context.db_port,
                            user=dawgie.context.db_path.split(':')[0])

def _cur (conn, real_dict=False):
    return conn.cursor (cursor_factory=psycopg2.extras.RealDictCursor) \
           if real_dict else conn.cursor()

def _fetchone (cur, text):
    try: result = cur.fetchone()[0]
    except: raise RuntimeError(text)
    return result

def _find (da:[dict], **kwds)->dict:
    '''search dictionary

    Finds the dictionary in the list that has all of the kwds and values given
    in the call as keywords.
    '''
    result = None
    for d in da:
        if all ([k in d for k in kwds]):
            if all ([d[k] == kwds[k] for k in kwds]):
                result = d
                break
            pass
        pass
    return result

def _prime_keys():
    conn = _conn()
    cur = _cur (conn, True)
    cur.execute('SELECT * from Prime;')
    ids = cur.fetchall()
    conn.commit()
    cur.close()
    cur = _cur (conn)
    cur.execute('SELECT PK,name from Target;')
    tgtn = dict([t for t in cur.fetchall()])
    cur.execute('SELECT PK,name from Task;')
    tskn = dict([t for t in cur.fetchall()])
    cur.execute('SELECT PK,name from Algorithm;')
    algn = dict([t for t in cur.fetchall()])
    cur.execute('SELECT PK,name from StateVector;')
    svn = dict([t for t in cur.fetchall()])
    cur.execute('SELECT PK,name from Value;')
    vn = dict([t for t in cur.fetchall()])
    conn.commit()
    cur.close()
    conn.close()
    keys = set()
    for i in ids: keys.add ('.'.join ([str(i['run_id']),
                                       tgtn[i['tn_id']],
                                       tskn[i['task_id']],
                                       algn[i['alg_id']],
                                       svn[i['sv_id']],
                                       vn[i['val_id']]]))
    return sorted([k for k in keys])

def _prime_values():
    conn = _conn()
    cur = _cur (conn)
    cur.execute('SELECT blob_name from Prime;')
    vals = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return [v[0] for v in vals]

def archive (done):
    bfn = dawgie.context.db_name + '.{:02d}.bck'
    path = dawgie.context.db_rotate_path

    if not (os.path.exists (path) and os.path.isdir (path)):
        raise ValueError('The path "' + path +
                         '" does not exist or is not a directory')

    for i in range (int(dawgie.context.db_rotate)-1,0,-1):
        ffn = os.path.join (path, bfn.format (i-1))
        nfn = os.path.join (path, bfn.format (i))

        if os.path.exists (ffn): shutil.move (ffn, nfn)
        pass
    args = ['/usr/bin/pg_dump',
            '-h', dawgie.context.db_host,
            '-p', '{0:d}'.format (dawgie.context.db_port),
            '-U', dawgie.context.db_path.split(':')[0],
            '-d', dawgie.context.db_name,
            '-f', os.path.join (path, bfn.format (0))]
    handler = ArchiveHandler(' '.join (args), done)
    twisted.internet.reactor.spawnProcess (handler, args[0], args=args, env=os.environ)
    return

def close(): return

def gather (anz, ans):
    if dawgie.db.post._db is None:
        raise RuntimeError('called connect before open')
    return Interface(anz, ans, '__all__')

def connect(alg, bot, tn):
    # attempt the connection, assume everything exists
    if not dawgie.db.post._db:raise RuntimeError('called connect before open')
    log.info ("connected")
    return Interface(alg, bot, tn)

# pylint: disable=unused-argument
def copy (dst, method, gateway):
    raise NotImplementedError('Not ready for postgresql')

def metrics()->'[dawgie.db.METRIC_DATA]':
    result = []
    svs = {}
    conn = dawgie.db.post._conn()
    cur = dawgie.db.post._cur (conn)
    cur.execute ('SELECT PK from StateVector WHERE name = %s;', ('__metric__',))
    sv_IDs = [t[0] for t in cur.fetchall()]
    cur.execute ('SELECT * from Prime WHERE sv_ID = ANY(%s);', (sv_IDs,))
    for row in cur.fetchall():
        key = (row[1], row[2], row[3], row[4])
        msv = svs[key] if key in svs else \
              dawgie.util.MetricStateVector(dawgie.METRIC(-2,-2,-2,-2,-2,-2),
                                            dawgie.METRIC(-2,-2,-2,-2,-2,-2))
        cur.execute ('SELECT name FROM Value WHERE PK = %s;', (row[6],))
        vn = cur.fetchone()[0]
        msv[vn] = dawgie.db.util.decode(row[7])
        svs[key] = msv
        pass
    for key,msv in svs.items():
        cur.execute ('SELECT name FROM Target where PK = %s;', (key[2],))
        target = cur.fetchone()[0]
        cur.execute ('SELECT name FROM Task where PK = %s;', (key[1],))
        task = cur.fetchone()[0]
        cur.execute ('SELECT name,design,implementation,bugfix FROM Algorithm '+
                     'where PK = %s;', (key[3],))
        alg = cur.fetchone()
        result.append (dawgie.db.METRIC_DATA(alg_name=alg[0],
                                             alg_ver=dawgie.VERSION(*alg[1:]),
                                             run_id=key[0], sv=msv,
                                             target=target, task=task))
        pass
    cur.close()
    conn.close()
    return result

# pylint: disable=redefined-builtin
def next():
    log.info ("in Next")
    # Get next run id
    if not dawgie.db.post._db: raise RuntimeError('called next before connect')

    # Insert value into Run table to increment the PK that serves as RUN ID
    conn = _conn()
    cur = _cur (conn)
    cur.execute('SELECT MAX(run_ID) from Prime;')
    runIDrow = cur.fetchone()
    runID = (runIDrow[0] if runIDrow and runIDrow[0] else 0) + 1
    conn.commit()
    cur.close()
    conn.close()
    return runID

# pylint: disable=redefined-builtin
def open():
    conn = _conn()
    cur = _cur (conn)
    # Make table for tasks
    # Target table has no version
    cur.execute('CREATE TABLE IF NOT EXISTS Target ' +
                '(PK bigserial primary key, name varchar(80) UNIQUE);')
    conn.commit()
    cur.execute('CREATE TABLE IF NOT EXISTS Task ' +
                '(PK bigserial primary key, name varchar(80) UNIQUE);')
    conn.commit()
    cur.execute('CREATE TABLE IF NOT EXISTS Algorithm ' +
                '(PK bigserial primary key, name varchar(80), ' +
                'task_ID bigserial references Task(PK), ' +
                'design integer, implementation integer, bugfix integer,' +
                'UNIQUE (name, task_ID, design, implementation, bugfix));')
    conn.commit()
    cur.execute('CREATE TABLE IF NOT EXISTS StateVector ' +
                '(PK bigserial primary key, name varchar(80), ' +
                'alg_ID bigserial references Algorithm(PK), ' +
                'design integer, implementation integer, bugfix integer,' +
                'UNIQUE (name, alg_ID, design, implementation, bugfix));')
    conn.commit()
    cur.execute('CREATE TABLE IF NOT EXISTS Value ' +
                '(PK bigserial primary key, name varchar(80), ' +
                'sv_ID bigserial references StateVector(PK), ' +
                'design integer, implementation integer, bugfix integer,' +
                'UNIQUE (name, sv_ID, design, implementation, bugfix));')
    conn.commit()
    cur.execute('CREATE TABLE IF NOT EXISTS Prime ' +
                '(PK bigserial primary key, run_ID integer, ' +
                'task_ID bigserial references Task(PK), ' +
                'tn_ID bigserial references Target(PK), ' +
                'alg_ID bigserial references Algorithm(PK), ' +
                'sv_ID bigserial references StateVector(PK), ' +
                'val_ID bigserial references Value(PK), ' +
                'blob_name varchar(100));')
    conn.commit()
    try:
        # Make sure all autoincremented sequences are set correctly
        # (incase of failed insert)
        cur.execute("SELECT pg_catalog.setval(pg_get_serial_sequence(" +
                    "'Prime', 'pk'), (SELECT MAX(PK) FROM Prime));")
        cur.execute("SELECT pg_catalog.setval(pg_get_serial_sequence(" +
                    "'Target', 'pk'), (SELECT MAX(PK) FROM Target));")
        cur.execute("SELECT pg_catalog.setval(pg_get_serial_sequence(" +
                    "'Algorithm', 'pk'), (SELECT MAX(PK) FROM Algorithm));")
        cur.execute("SELECT pg_catalog.setval(pg_get_serial_sequence" +
                    "('StateVector', 'pk'), (SELECT MAX(PK) FROM " +
                    "StateVector));")
        cur.execute("SELECT pg_catalog.setval(pg_get_serial_sequence(" +
                    "'Value', 'pk'), (SELECT MAX(PK) FROM Value));")
        cur.execute("SELECT pg_catalog.setval(pg_get_serial_sequence(" +
                    "'Task', 'pk'), (SELECT MAX(PK) FROM Task));")
    except psycopg2.ProgrammingError: pass
    log.info ("finished making or updating table sequences")
    conn.commit()
    cur.close()
    conn.close()
    dawgie.db.post._db = True
    return

def remove (runid):
    # Remove all rows with the given run ID from the primary table
    conn = _conn()
    cur = _cur (conn)
    cur.execute('REMOVE FROM Prime WHERE run_ID = %s;', [runid])
    conn.commit()
    cur.close()
    conn.close()
    return

def reopen():
    if not dawgie.db.post._db: open()
    return

def reset (runid:int, tn:str, tskn, alg)->None:
    conn = dawgie.db.post._conn()
    cur = dawgie.db.post._cur (conn)
    cur.execute('SELECT * from Target WHERE name = %s;', [tn])
    tn_ID = _fetchone(cur,'Dataset: Could not find target ID')
    cur.execute('SELECT * from TASK WHERE name = %s;', [tskn])
    task_ID = _fetchone (cur, 'Dataset load: Could not find task ID')
    cur.execute('SELECT pk FROM Algorithm WHERE name = %s AND task_ID = %s;',
                [alg.name(), task_ID])
    alg_ID = list(set([pk[0] for pk in cur.fetchall()]))
    algv = set()
    for sv in alg.state_vectors():
        cur.execute('SELECT pk FROM StateVector WHERE name = %s AND ' +
                    'alg_ID = ANY(%s);', [sv.name(), alg_ID])
        sv_ID = list(set([pk[0] for pk in cur.fetchall()]))
        cur.execute('SELECT alg_ID, sv_ID FROM Prime WHERE run_ID = %s AND ' +
                    ' tn_ID = %s AND task_ID = %s AND alg_ID = ANY(%s) AND ' +
                    'sv_ID = ANY(%s);',
                    [str(runid), tn_ID, task_ID, alg_ID, sv_ID])
        ids = cur.fetchall()
        algv.update (set([fk[0] for fk in ids]))
        svv = set([fk[1] for fk in ids])

        if len (svv) == 1:
            cur.execute ('SELECT design,implementation,bugfix '+
                         'FROM StateVector WHERE PK = %s;', [svv.pop()])
            v = cur.fetchone()
            sv._set_ver (dawgie.VERSION(v[0],v[1],v[2]))
        else: log.critical ('Dataset load: The postgres db is corrupt ' +
                            'because found %d IDs for the specific state ' +
                            'vector %s', len (svv), '.'.join ([str (runid),
                                                               tn, tskn,
                                                               alg.name(),
                                                               sv.name()]))
        pass
    if len (algv) == 1:
        cur.execute ('SELECT design,implementation,bugfix '+
                     'FROM Algorithm WHERE PK = %s;', [algv.pop()])
        v = cur.fetchone()
        alg._set_ver (dawgie.VERSION(v[0],v[1],v[2]))
    else: log.critical ('Dataset load: The postgres db is corrupt ' +
                        'because found %d IDs for the specific algorithm %s',
                        len (svv),
                        '.'.join ([str (runid), tn, tskn, alg.name()]))
    conn.commit()
    cur.close()
    conn.close()
    return

def retreat (reg, ret):
    if dawgie.db.post._db is None:
        raise RuntimeError('called connect before open')
    return Interface(reg, ret, ret._target())

def targets():
    log.info ("in targets()")
    conn = _conn()
    cur = _cur (conn)
    cur.execute('SELECT name from Target;')
    result = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in result]

def trace (task_alg_names):
    target_list = dawgie.db.targets()
    conn = _conn()
    cur = _cur (conn)
    result = {}
    for tn in target_list:
        result[tn] = {}
        for tan in task_alg_names:
            tskn,algn = tan.split('.')
            cur.execute ('SELECT PK FROM Target WHERE name = ANY(%s);',
                         [['__all__', tn]])
            tnids = cur.fetchall()
            cur.execute ('SELECT PK FROM Task WHERE name = %s;', [tskn])
            tid = cur.fetchone()
            cur.execute ('SELECT MAX(design),MAX(implementation),MAX(bugfix) '+
                         'FROM Algorithm WHERE task_ID = %s AND name = %s;',
                         [tid, algn])
            version = cur.fetchone()
            cur.execute ('SELECT PK FROM Algorithm WHERE task_ID = %s AND ' +
                         'name = %s AND design = %s AND implementation = %s ' +
                         'AND bugfix = %s;',
                         [tid, algn, version[0], version[1], version[2]])
            aid = cur.fetchone()
            cur.execute ('SELECT run_ID FROM Prime WHERE ' +
                         'tn_ID = ANY(%s) AND task_ID = %s AND alg_ID = %s;',
                         [tnids, tid, aid])
            runid = cur.fetchall()

            if not runid: result[tn][tan] = None
            else: result[tn][tan] = max([r[0] for r in runid])
            pass
        pass
    return result

def update (tsk, alg, sv, vn, v):
    log.info ("In databse update")
    # Just adds these things to their respective tables
    # Check if connection to DB is already open
    if not dawgie.db.post._db: raise RuntimeError('Called before open')

    conn = _conn()
    cur = _cur (conn)
    # Add stuff. Check if they already exist in the tables first.
    try:
        cur.execute ('INSERT into Task(name) values (%s);', [tsk._name()])
        conn.commit()
    except psycopg2.IntegrityError: conn.rollback()
    cur.execute('SELECT pk from TASK WHERE name = %s;', [tsk._name()])
    task_ID = cur.fetchone()
    task_ID = task_ID[0]
    try:
        cur.execute('INSERT into Algorithm(name, task_ID, design, '+
                    'implementation, bugfix) values ' +
                    '(%s, %s, %s, %s, %s);',
                    (alg.name(), task_ID, alg.design(),
                     alg.implementation(), alg.bugfix()))
        conn.commit()
    except psycopg2.IntegrityError: conn.rollback()

    if sv:
        cur.execute('SELECT pk from Algorithm WHERE name = %s and task_ID = %s'+
                    ' and design = %s and implementation = %s and bugfix = %s;',
                    (alg.name(), task_ID,
                     alg.design(), alg.implementation(), alg.bugfix()))
        alg_ID = cur.fetchone()[0]
        try:
            cur.execute('INSERT into StateVector(name, alg_ID, ' +
                        'design, implementation, bugfix) values ' +
                        '(%s, %s, %s, %s, %s);',
                        (sv.name(), alg_ID, sv.design(),
                         sv.implementation(), sv.bugfix()))
            conn.commit()
        except psycopg2.IntegrityError: conn.rollback()
        cur.execute('SELECT pk from StateVector WHERE name = %s and alg_ID = %s ' +
                    'and design = %s and implementation = %s and bugfix = %s;',
                    (sv.name(), alg_ID,
                     sv.design(), sv.implementation(), sv.bugfix()))
        sv_ID = cur.fetchone()[0]
        try:
            cur.execute('INSERT into Value(name, sv_ID, design, ' +
                        'implementation, bugfix) values ' +
                        '(%s, %s, %s, %s, %s);',
                        (vn, sv_ID,
                         v.design(), v.implementation(), v.bugfix()))
            conn.commit()
        except psycopg2.IntegrityError: conn.rollback()
        pass

    cur.close()
    conn.close()
    return

def versions():
    # Returns Algorithm, StateVector, and Value as a list of dictionaries
    # where each dictionary represents a row in the table
    log.info ('versions() - starting')
    conn = _conn()
    cur = _cur (conn, True)
    alg_ver = {}
    sv_ver = {}
    task_ver = {}
    v_ver = {}
    cur.execute('SELECT * from Task;')
    tsk = cur.fetchall()
    for t in tsk: task_ver[t['name']] = True
    cur.execute('SELECT * from Algorithm;')
    alg = cur.fetchall()
    for a in alg: _append_ver (alg_ver,
                               '.'.join([_find (tsk, pk=a['task_id'])['name'],
                                         a['name']]),
                               MyVersion(a['design'],
                                         a['implementation'],
                                         a['bugfix']).asstring())
    cur.execute('SELECT * from StateVector;')
    svs = cur.fetchall()
    for sv in svs: _append_ver (sv_ver,
                                '.'.join([_find (tsk, pk=_find (alg, pk=sv['alg_id'])['task_id'])['name'],
                                          _find (alg, pk=sv['alg_id'])['name'],
                                          sv['name']]),
                                MyVersion(sv['design'],
                                          sv['implementation'],
                                          sv['bugfix']).asstring())
    cur.execute('SELECT * from Value;')
    vals = cur.fetchall()
    for v in vals: _append_ver (v_ver,
                                '.'.join ([_find (tsk, pk=_find (alg, pk=_find (svs, pk=v['sv_id'])['alg_id'])['task_id'])['name'],
                                           _find (alg, pk=_find (svs, pk=v['sv_id'])['alg_id'])['name'],
                                           _find (svs, pk=v['sv_id'])['name'],
                                           v['name']]),
                                MyVersion(v['design'],
                                          v['implementation'],
                                          v['bugfix']).asstring())
    conn.commit()
    cur.close()
    conn.close()
    log.info ('versions() - starting')
    return task_ver, alg_ver, sv_ver, v_ver

def view_locks(): return {'msg':'<h1>Not Applicable with postgresql database',
                          'tasks':[]}
