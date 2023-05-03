'''Postgresql implementation

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

# pylint: disable=import-self,protected-access

import collections
import dawgie
import dawgie.context
import dawgie.db
from dawgie.db import REF
import dawgie.db.post
import dawgie.db.util
import dawgie.db.util.aspect
import dawgie.util
import logging; log = logging.getLogger(__name__)
import os
import pickle
import psycopg
import psycopg.rows
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
            # more readable this way so pylint: disable=logging-not-lazy
            # exceptions always look the same; pylint: disable=duplicate-code
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
        # Get rows from prime table that have these algorithm primary keys
        cur.execute('SELECT val_ID,blob_name from Prime WHERE run_ID = %s ' +
                    'and alg_ID = %s and tn_ID = %s ' +
                    'and task_ID = %s and sv_ID = %s;',
                    (run_ID, alg_ID, tn_ID, task_ID, sv_ID))
        runs = cur.fetchall()

        if not runs: log.info ('Dataset load: Could not find any runs that match given values')

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
        # modifying table in loop so pylint: disable=unnecessary-comprehension
        for k1 in [k for k in table]:
            for k2 in [k for k in table[k1]]:
                if not table[k1][k2]:
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

    def __tn_id (self, conn, cur, tn=None):
        tn = tn if tn else self._tn()
        # Get target id that matches target name or create it if not there
        try:
            cur.execute('INSERT into Target (name) values (%s)', [tn])
            conn.commit()
        except psycopg.IntegrityError: conn.rollback()
        except psycopg.ProgrammingError: conn.rollback()  # permission issue
        cur.execute('SELECT * from Target WHERE name = %s;', [tn])
        tn_ID = _fetchone(cur,'Dataset: Could not find target ID')
        return tn_ID

    def _ckeys (self, l1k, l2k):
        if l2k: keys = self.__span['table'][l1k][l2k].keys()
        elif l1k: keys = self.__span['table'][l1k].keys()
        elif 'table' in self.__span: keys = self.__span['table'].keys()
        else: keys = []
        return keys

    def _collect (self, refs:[(dawgie.SV_REF, dawgie.V_REF)])->None:
        # pylint: disable=too-many-locals
        conn = dawgie.db.post._conn()
        cur = dawgie.db.post._cur (conn)
        self.__span = {'sv_templates':
                       {'.'.join ([dawgie.util.task_name (ref.factory),
                                   ref.impl.name(),
                                   ref.item.name()]):pickle.dumps (ref.item)
                        for ref in refs},
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
                run_ID = {rid[0] for rid in cur.fetchall()}

                if not run_ID:
                    # long message more readable pylint: disable=logging-not-lazy
                    log.warning ('Aspect collect: Could not find any runids ' +
                                 'for target %s and %s', tn, str (ref))
                    continue

                run_ID = max (run_ID) if 1 < len (run_ID) else run_ID.pop()
                # long message more readable so pylint: disable=logging-not-lazy
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
                    else:
                        # long msg readable so pylint: disable=logging-not-lazy
                        log.critical ('Need to improve compliant because ' +
                                      'received soemthing that was neither ' +
                                      'SV_REF or V_REF: ' + str (type (ref)))
                        pass
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
        # Take highest run number row from prime table for that task,
        #   algorithm, state vector if current run does not exist in
        #   Primary table.
        # pylint: disable=too-many-locals,too-many-statements
        if self._alg().abort(): raise dawgie.AbortAEError()

        log.debug ("In Interface load")
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
                raise KeyError(f'Unknown factory type {algref.factory.__name__}')

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
            alg_ID = list({pk[0] for pk in cur.fetchall()})
            msv = dawgie.util.MetricStateVector(dawgie.METRIC(-1,-1,-1,-1,-1,-1),
                                                dawgie.METRIC(-1,-1,-1,-1,-1,-1))
            for sv in self._alg().state_vectors() + [msv]:
                cur.execute('SELECT pk FROM StateVector WHERE name = %s AND ' +
                            'alg_ID = ANY(%s);', [sv.name(), alg_ID])
                sv_ID = list({pk[0] for pk in cur.fetchall()})
                cur.execute('SELECT run_ID FROM Prime WHERE tn_ID = %s AND ' +
                            'task_ID = %s AND alg_ID = ANY(%s) AND '+
                            'sv_ID = ANY(%s);',
                            [tn_ID, task_ID, alg_ID, sv_ID])
                run_ID = {pk[0] for pk in cur.fetchall()}

                if not run_ID:
                    # long msg more readable so pylint: disable=logging-not-lazy
                    log.debug ('Dataset load: Could not find any runs that ' +
                               'match given the algorithm and state vector')
                    continue

                run_ID = self._runid() if self._runid() in run_ID \
                                       else max(run_ID)
                cur.execute ('SELECT alg_ID,sv_ID FROM Prime WHERE ' +
                             'run_ID = %s AND tn_ID = %s AND task_ID = %s '+
                             ' AND alg_ID = ANY(%s) and sv_ID = ANY(%s);',
                             [run_ID, tn_ID, task_ID, alg_ID, sv_ID])
                narrowed = set(cur.fetchall())

                if len (narrowed) != 1:
                    # long msg more readable so pylint: disable=logging-not-lazy
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

    def _recede (self, refs:[(dawgie.SV_REF, dawgie.V_REF)])->None:
        # pylint: disable=too-many-locals,too-many-statements
        conn = dawgie.db.post._conn()
        cur = dawgie.db.post._cur (conn)
        self.__span = {'sv_templates':
                       {'.'.join ([dawgie.util.task_name (ref.factory),
                                   ref.impl.name(),
                                   ref.item.name()]):pickle.dumps (ref.item)
                        for ref in refs},
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
            alg_IDs = [aid[0] for aid in cur.fetchall()]
            cur.execute('SELECT PK FROM StateVector WHERE name = %s and ' +
                        'alg_ID = ANY(%s);',
                        (ref.item.name(), alg_IDs,))
            sv_IDs = [svid[0] for svid in cur.fetchall()]
            fsvn = '.'.join ([dawgie.util.task_name (ref.factory),
                              ref.impl.name(),
                              ref.item.name()])
            cur.execute ('SELECT run_ID FROM Prime WHERE tn_ID = %s AND ' +
                         'task_ID = %s AND alg_ID = ANY(%s) AND ' +
                         'sv_ID = ANY(%s);', [tnid, task_ID, alg_IDs, sv_IDs])
            rids = sorted ({r[0] for r in cur.fetchall()})
            for rid in rids:
                cur.execute ('SELECT PK,alg_ID,sv_ID FROM Prime WHERE ' +
                             'run_ID = %s AND  tn_ID = %s AND ' +
                             'task_ID = %s AND alg_ID = ANY(%s) AND ' +
                             'sv_ID = ANY(%s);',
                             [rid, tnid, task_ID, alg_IDs, sv_IDs])
                ids = cur.fetchall()
                pks = [id[0] for id in ids]
                alg_ID,sv_ID = ids[pks.index(max(pks))][1:]
                cur.execute('SELECT val_ID from Prime WHERE run_ID = %s AND ' +
                            'alg_ID = %s AND tn_ID = %s and task_ID = %s and ' +
                            'sv_ID = %s;',
                            (rid, alg_ID, tnid, task_ID, sv_ID))
                vids = [vid[0] for vid in cur.fetchall()]

                if not vids:
                    # long msg more readable so pylint: disable=logging-not-lazy
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
                    else: log.critical ('Need to improve compliant because received soemthing that was neither SV_REF or V_REF: %s', str (type (ref)))
                    pass
                pass
            pass
        conn.commit()
        cur.close()
        conn.close()
        self.__purge()
        return

    def _retarget (self,subname:str,upstream:[dawgie.ALG_REF])->dawgie.Dataset:
        conn = dawgie.db.post._conn()
        cur = dawgie.db.post._cur (conn)
        target_ID = self.__tn_id (conn, cur)
        subname_ID = self.__tn_id (conn, cur, subname)
        log.debug ('retarget "%s"[%d] as "%s"[%d]',
                   self._tn(), target_ID, subname, subname_ID)
        for ref in upstream:
            cur.execute ('SELECT PK FROM Task WHERE name = %s;',
                         [dawgie.util.task_name (ref.factory)])
            task_ID = cur.fetchone()[0]
            cur.execute('SELECT PK from Algorithm WHERE name = %s and ' +
                        'task_ID = %s and ' +
                        'design = %s and implementation = %s and bugfix = %s;',
                        (ref.impl.name(), task_ID, ref.impl.design(),
                         ref.impl.implementation(), ref.impl.bugfix()))
            alg_ID = cur.fetchone()[0]
            cur.execute ('SELECT run_ID FROM Prime WHERE tn_ID = %s AND ' +
                         'task_ID = %s AND alg_ID = %s;',
                         [target_ID, task_ID, alg_ID])
            rid = max(r[0] for r in cur.fetchall())
            cur.execute ('SELECT sv_ID,val_ID,blob_name FROM Prime WHERE ' +
                         'run_ID = %s AND tn_ID = %s AND task_ID = %s AND ' +
                         'alg_ID = %s;', [rid, target_ID, task_ID, alg_ID])
            for sv_ID,val_ID,bn in cur.fetchall():
                cur.execute ('SELECT EXISTS (SELECT 1 FROM Prime WHERE ' +
                             'run_ID = %s AND tn_ID = %s AND task_ID = %s ' +
                             'AND alg_ID = %s AND sv_ID = %s AND val_ID = %s ' +
                             'AND blob_name = %s);',
                             [rid,subname_ID,task_ID,alg_ID,sv_ID,val_ID,bn])
                already_exists = cur.fetchone()[0]
                log.debug ('retarget %s: %s',
                           ('exists' if already_exists else 'does not exist'),
                           str([rid,subname_ID,task_ID,alg_ID,sv_ID,val_ID,bn]))
                if not already_exists:
                    cur.execute ('INSERT INTO Prime ' +
                                 '(run_ID, tn_ID, task_ID, alg_ID, sv_ID, ' +
                                 'val_ID, blob_name) values ' +
                                 '(%s, %s, %s, %s, %s, %s, %s);',
                                 [rid,subname_ID,task_ID,alg_ID,sv_ID,val_ID,bn])
                    conn.commit()
                    pass
                pass
            pass
        conn.commit()
        cur.close()
        conn.close()
        return Interface(self._alg(), self._bot(), subname)

    def _update (self):
        # pylint: disable=too-many-locals,too-many-statements
        if self._alg().abort(): raise dawgie.AbortAEError()

        log.debug ("in Interface update")
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
                self._bot().new_values (('.'.join ([str (self._runid()),
                                                    self._tn(),
                                                    self._task(),
                                                    self._alg().name(),
                                                    sv.name(), vn]),
                                         not exists))

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
                if not dawgie.db.util.verify (val):
                    log.critical ('offending item is %s',
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
                    except psycopg.IntegrityError: conn.rollback()
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
            # exceptions always look the same; pylint: disable=duplicate-code
            raise dawgie.NotValidImplementationError\
                  ('StateVector contains data that does not extend ' +
                   'dawgie.Value correctly. See log for details.')

        while primes:
            cur = dawgie.db.post._cur (conn)
            try:
                for args in primes: cur.execute (*args)
                conn.commit()
                primes.clear()
            except psycopg.IntegrityError: conn.rollback()
            pass
        cur.close()
        conn.close()
        return

    def _update_msv (self, msv):
        # pylint: disable=too-many-locals,too-many-statements
        if self._alg().abort(): raise dawgie.AbortAEError()

        log.debug ("in Interface update process metrics")
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
                except psycopg.IntegrityError: conn.rollback()
                cur.execute (*args)
                sv_ID = cur.fetchone()
                pass

            # Get the value id that matches the value
            if not dawgie.db.util.verify (val):
                log.critical ('offending item is %s',
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
                except psycopg.IntegrityError: conn.rollback()
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
            # exceptions always look the same; pylint: disable=duplicate-code
            raise dawgie.NotValidImplementationError\
                  ('MetricStateVector contains data that does not extend ' +
                   'dawgie.Value correctly. See log for details.')

        while primes:
            cur = dawgie.db.post._cur (conn)
            try:
                for args in primes: cur.execute (*args)
                conn.commit()
                primes.clear()
            except psycopg.IntegrityError: conn.rollback()
            pass
        cur.close()
        conn.close()
        return

    def ds(self): return self
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
    uri = f'postgresql://{dawgie.context.db_path}@{dawgie.context.db_host}:{dawgie.context.db_port}/{dawgie.context.db_name}'
    log.debug ('using URI: %s', uri)
    return psycopg.connect(uri)

def _cur (conn, real_dict=False):
    return conn.cursor (row_factory=psycopg.rows.dict_row) \
           if real_dict else conn.cursor()

def _fetchone (cur, text):
    try: result = cur.fetchone()[0]
    except:
        # error msg should be text so pylint: disable=raise-missing-from
        raise RuntimeError(text)
    return result

def _find (da:[dict], **kwds)->dict:
    '''search dictionary

    Finds the dictionary in the list that has all of the kwds and values given
    in the call as keywords.
    '''
    result = None
    for d in da:
        if all ((k in d for k in kwds)):
            if all ((d[k] == v for k,v in kwds.items())):
                result = d
                break
            pass
        pass
    return result

def _prime_keys():
    if not dawgie.db.post._db:
        raise RuntimeError('called _prime_keys before open')

    conn = _conn()
    cur = _cur (conn, True)
    cur.execute('SELECT * from Prime;')
    ids = cur.fetchall()
    conn.commit()
    cur.close()
    cur = _cur (conn)
    cur.execute('SELECT PK,name from Target;')
    tgtn = dict(cur.fetchall())
    cur.execute('SELECT PK,name from Task;')
    tskn = dict(cur.fetchall())
    cur.execute('SELECT PK,name from Algorithm;')
    algn = dict(cur.fetchall())
    cur.execute('SELECT PK,name from StateVector;')
    svn = dict(cur.fetchall())
    cur.execute('SELECT PK,name from Value;')
    vn = dict(cur.fetchall())
    conn.commit()
    cur.close()
    conn.close()
    keys = {('.'.join ([str(i['run_id']),
                        tgtn[i['tn_id']],
                        tskn[i['task_id']],
                        algn[i['alg_id']],
                        svn[i['sv_id']],
                        vn[i['val_id']]])) for i in ids}
    return sorted(keys)

def _prime_values():
    if not dawgie.db.post._db:
        raise RuntimeError('called _prime_values before open')

    conn = _conn()
    cur = _cur (conn)
    cur.execute('SELECT blob_name from Prime;')
    vals = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return [v[0] for v in vals]

def add (target_name:str)->bool:
    if not dawgie.db.post._db: raise RuntimeError('called connect before open')

    conn = _conn()
    cur = _cur (conn, True)
    exists = False
    cur.execute('SELECT pk from Target WHERE name = %s;', [target_name])
    pk = cur.fetchone()

    if pk: exists = len (pk) == 1
    else:
        try:
            cur.execute('INSERT into Target (name) values (%s)', [target_name])
            conn.commit()
            exists = True
        except psycopg.IntegrityError: conn.rollback()
        except psycopg.ProgrammingError: conn.rollback()  # permission issue
    cur.close()
    conn.close()
    return exists

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
            '-p', f'{dawgie.context.db_port:d}',
            '-U', dawgie.context.db_path.split(':')[0],
            '-d', dawgie.context.db_name,
            '-f', os.path.join (path, bfn.format (0))]
    handler = ArchiveHandler(' '.join (args), done)
    twisted.internet.reactor.spawnProcess (handler, args[0], args=args, env=os.environ)
    return

def close():
    dawgie.db.post._db = False
    return

def connect(alg, bot, tn):
    # attempt the connection, assume everything exists
    if not dawgie.db.post._db: raise RuntimeError('called connect before open')
    log.debug ("connected")
    return Interface(alg, bot, tn)

def consistent (inputs:[REF], outputs:[REF], target_name:str)->():
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    if not dawgie.db.post._db:
        raise RuntimeError('called consistent before open')

    conn = dawgie.db.post._conn()
    cur = dawgie.db.post._cur (conn)
    cur.execute('SELECT pk FROM Target WHERE name = %s;', [target_name])
    tn_ID = _fetchone(cur, f'Target "{target_name}" is listed more than once')
    # 1: Find all the times this version ran and collect the run IDs
    o_runids = []
    for output in outputs:
        cur.execute('SELECT pk FROM Task WHERE name = %s;', [output.tid.name])
        task_ID = _fetchone (cur, (f'Task "{output.tid.name}" is listed more than once'))
        cur.execute('SELECT pk FROM Algorithm WHERE name = %s AND ' +
                    'task_ID = %s AND design = %s AND implementation = %s ' +
                    'AND bugfix = %s;',
                    (output.aid.name, task_ID, output.aid.version.design(),
                     output.aid.version.implementation(),
                     output.aid.version.bugfix()))
        alg_ID = _fetchone (cur, f'consistent(): Algorithm "{output.aid.name} {output.aid.version.asstring()}" is not singular')
        cur.execute('SELECT pk FROM StateVector WHERE name = %s AND ' +
                    'alg_ID = %s AND design = %s AND implementation = %s ' +
                    'AND bugfix = %s;',
                    (output.sid.name, alg_ID, output.sid.version.design(),
                     output.sid.version.implementation(),
                     output.sid.version.bugfix()))
        sv_ID = _fetchone (cur, f'consistent(): SV "{output.sid.name} {output.sid.version.asstring()}" is not singular')
        cur.execute('SELECT pk FROM Value WHERE name = %s AND ' +
                    'sv_ID = %s AND design = %s AND implementation = %s ' +
                    'AND bugfix = %s;',
                    (output.vid.name, sv_ID, output.vid.version.design(),
                     output.vid.version.implementation(),
                     output.vid.version.bugfix()))
        v_ID = _fetchone (cur, f'consistent(): Value "{output.vid.name} {output.vid.version.asstring()}" is not singular')
        cur.execute('SELECT run_ID FROM Prime WHERE tn_ID = %s AND ' +
                    'task_ID = %s AND alg_ID = %s AND sv_ID = %s AND ' +
                    'val_ID = %s;',
                    [tn_ID, task_ID, alg_ID, sv_ID, v_ID])
        o_runids.append ({runid[0] for runid in cur.fetchall()})
        pass
    o_runids = sorted (set.intersection (*o_runids), reverse=True)

    # 2: If there are no run IDs with this output, then return empty tuple
    if not o_runids:
        cur.close()
        conn.close()
        log.debug ('step 1: no run ids with this output')
        return tuple()

    # 3: Find all of the inputs keyed by name and save runid,blobname
    i_runids = {}
    ridbns = {}
    for inp in inputs:
        key = '.'.join ([inp.tid.name, inp.aid.name])
        if key not in i_runids: i_runids[key] = []
        if key not in ridbns: ridbns[key] = []

        cur.execute('SELECT pk FROM Task WHERE name = %s;', [inp.tid.name])
        task_ID = _fetchone (cur, f'Task "{inp.tid.name}" is listed more than once')
        cur.execute('SELECT pk FROM Algorithm WHERE name = %s AND ' +
                    'task_ID = %s;', (inp.aid.name, task_ID))
        alg_IDs = list({pk[0] for pk in cur.fetchall()})
        cur.execute('SELECT pk FROM StateVector WHERE name = %s AND ' +
                    'alg_ID = ANY(%s);', [inp.sid.name, alg_IDs])
        sv_IDs = list({pk[0] for pk in cur.fetchall()})
        cur.execute('SELECT pk FROM Value WHERE name = %s AND sv_ID = ANY(%s);',
                    [inp.vid.name, sv_IDs])
        val_IDs = list({pk[0] for pk in cur.fetchall()})
        cur.execute('SELECT run_ID,blob_name FROM Prime WHERE tn_ID = %s AND '+
                    'task_ID = %s AND alg_ID = ANY(%s) AND ' +
                    'sv_ID = ANY(%s) AND val_ID = ANY(%s);',
                    [tn_ID, task_ID, alg_IDs, sv_IDs, val_IDs])
        ridbns[key].append (sorted (cur.fetchall(), key=lambda t:t[0]))
        kval = ridbns[key][-1][0][1]
        i_runids[key].append ({runid for runid,_bn in filter
                               (lambda t,k=kval:t[1] == k, ridbns[key][-1])})
        pass
    for key in i_runids.copy():
        i_runids[key] = sorted (set.intersection (*i_runids[key]),
                                reverse=True)
        pass

    # 4: If there are no run input IDs with version, then return empty tuple
    if any((not v for v in i_runids.values())):
        cur.close()
        conn.close()
        log.debug ('Step 3: no input runids - %s %s', str(key), str(i_runids))
        return tuple()

    # 5: Use runids from (1) and (3) to find when in time to promote
    # -- Here is the trick:
    # --   Use the m_runids to find the corresponding i_runids. If they match
    # --   and the input matching the constraint has the good runid in both
    # --   the we can promote. Matching constraints was done in (5) by reducing
    # --   possible outputs to between matching blob rids and all rids for that
    # --   constraint. Therefore only to check that there is a consistent runid
    # --   for i_runids and m_runids.
    runid = None
    for rid in o_runids:
        match = {key:-3 for key in i_runids}
        for key,value in i_runids.items():
            m = -2
            for r in value:
                if r <= rid:
                    m = r
                    break
                pass
            match[key] = m
            pass

        if all ((0 <= vrid for vrid in match.values())):
            runid = rid
            break
        pass

    # 6: If no workable runID found, then return empty tuple
    if not runid:
        cur.close()
        conn.close()
        log.debug ('step 5: no run ids found -- %s %s',
                   str(o_runids), str(i_runids))
        return tuple()

    # 7: Build the juncture from the runid and output
    juncture = []
    for output in outputs:
        cur.execute('SELECT pk FROM Task WHERE name = %s;', [output.tid.name])
        task_ID = _fetchone (cur, f'Task "{output.tid.name}" is listed more than once')
        cur.execute('SELECT pk FROM Algorithm WHERE name = %s AND ' +
                    'task_ID = %s AND design = %s AND implementation = %s ' +
                    'AND bugfix = %s;',
                    (output.aid.name, task_ID, output.aid.version.design(),
                     output.aid.version.implementation(),
                     output.aid.version.bugfix()))
        alg_ID = _fetchone (cur, f'consistent(): Algorithm "{output.aid.name} {output.aid.version.asstring()}" is not singular')
        cur.execute('SELECT pk FROM StateVector WHERE name = %s AND ' +
                    'alg_ID = %s AND design = %s AND implementation = %s ' +
                    'AND bugfix = %s;',
                    (output.sid.name, alg_ID, output.sid.version.design(),
                     output.sid.version.implementation(),
                     output.sid.version.bugfix()))
        sv_ID = _fetchone (cur, f'consistent(): SV "{output.sid.name} {output.sid.version.asstring()}" is not singular')
        cur.execute('SELECT pk FROM Value WHERE name = %s AND ' +
                    'sv_ID = %s AND design = %s AND implementation = %s ' +
                    'AND bugfix = %s;',
                    (output.vid.name, sv_ID, output.vid.version.design(),
                     output.vid.version.implementation(),
                     output.vid.version.bugfix()))
        v_ID = _fetchone (cur, f'consistent(): Value "{output.vid.name} {output.vid.version.asstring()}" is not singular')
        cur.execute('SELECT blob_name FROM Prime WHERE run_id = %s AND ' +
                    'tn_ID = %s AND task_ID = %s AND alg_ID = %s AND ' +
                    'sv_ID = %s AND val_ID = %s;',
                    [runid, tn_ID, task_ID, alg_ID, sv_ID, v_ID])
        bn = _fetchone (cur, 'No matchiing entry')
        juncture.append ((tn_ID, task_ID, alg_ID, sv_ID, v_ID, bn))
        pass
    cur.close()
    conn.close()
    return juncture

def copy (_dst, _method, _gateway):
    raise NotImplementedError('Not ready for postgresql')

def gather (anz, ans):
    if not dawgie.db.post._db: raise RuntimeError('called gather before open')
    return Interface(anz, ans, '__all__')

def metrics()->'[dawgie.db.METRIC_DATA]':
    if not dawgie.db.post._db: raise RuntimeError('called metrics before open')

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
        try:
            msv[vn] = dawgie.db.util.decode(row[7])
            svs[key] = msv
        except FileNotFoundError: log.error ('possible database corruption because cannot find __metric__ state vector value: %s', row[7])
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
    log.debug ("in Next")
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
    except psycopg.ProgrammingError: pass
    conn.commit()
    cur.close()
    conn.close()
    dawgie.db.post._db = True
    return

def promote (juncture:(), runid:int):
    # to test or not to test? Should it be checked (can it be?) that the primary
    # table does not contain a similar entry already?
    #
    # Test:
    #    Get all of the known primary tables with the run id then make sure that
    #    that a different version of same value is not already written. Throw an
    #    exception if something already exists or just log it? Log at first to
    #    prevent killing of main twisted thread.
    if not dawgie.db.post._db: raise RuntimeError('called promote before open')

    conn = dawgie.db.post._conn()
    cur = dawgie.db.post._cur (conn)
    entries = []
    for tn_ID,task_ID,alg_ID,sv_ID,v_ID,_bn in juncture:
        cur.execute('SELECT blob_name FROM Prime WHERE run_ID = %s AND ' +
                    'tn_ID = %s AND task_ID = %s AND alg_ID = %s AND ' +
                    'sv_ID = %s AND val_ID = %s;',
                    [runid, tn_ID, task_ID, alg_ID, sv_ID, v_ID])
        entries.extend ([e[0] if e else None for e in cur.fetchall()])
        pass
    cur.close()
    conn.close()

    if any((e is not None for e in entries)): return False

    conn = dawgie.db.post._conn()
    cur = dawgie.db.post._cur (conn)
    try:
        for tn_ID,task_ID,alg_ID,sv_ID,v_ID,bn in juncture:
            cur.execute('INSERT INTO Prime (run_ID, tn_ID, task_ID, ' +
                        'alg_ID, sv_ID, val_ID, blob_name) values ' +
                        '(%s, %s, %s, %s, %s, %s, %s);',
                        [runid, tn_ID, task_ID, alg_ID, sv_ID, v_ID, bn])
            pass
        conn.commit()
    except psycopg.IntegrityError:
        conn.rollback()
        cur.close()
        conn.close()
        return False
    cur.close()
    conn.close()
    return True

# pylint: disable=too-many-arguments
def remove (runid:int, tn:str, tskn:str, algn:str, svn:str, vn:str):
    if not dawgie.db.post._db: raise RuntimeError('called remove before open')

    # Remove all rows with the given run ID from the primary table
    removed = tuple()
    conn = _conn()
    cur = _cur (conn)
    cur.execute('SELECT * from Target WHERE name = %s;', [tn])
    tn_ID = _fetchone(cur,'Dataset: Could not find target ID')
    cur.execute('SELECT * from TASK WHERE name = %s;', [tskn])
    task_ID = _fetchone (cur, 'Dataset load: Could not find task ID')
    cur.execute('SELECT pk FROM Algorithm WHERE name = %s AND task_ID = %s;',
                [algn, task_ID])
    alg_ID = list({pk[0] for pk in cur.fetchall()})
    cur.execute('SELECT pk FROM StateVector WHERE name = %s AND ' +
                'alg_ID = ANY(%s);', [svn, alg_ID])
    sv_ID = list({pk[0] for pk in cur.fetchall()})
    cur.execute('SELECT pk FROM Value WHERE name = %s AND ' +
                'sv_ID = ANY(%s);', [vn, sv_ID])
    val_ID = list({pk[0] for pk in cur.fetchall()})

    cur.execute('DELETE FROM Prime WHERE run_ID = %s AND tn_ID = %s AND ' +
                'task_ID = %s AND alg_ID = ANY(%s) AND sv_ID = ANY(%s) AND ' +
                'val_ID = ANY(%s);',
                [runid, tn_ID, task_ID, alg_ID, sv_ID, val_ID])
    removed = (runid, tn_ID, task_ID, alg_ID, sv_ID, val_ID)
    conn.commit()
    cur.close()
    conn.close()
    return removed

def reopen()->bool:
    already_open = False

    if not dawgie.db.post._db: open()
    else: already_open = True

    return already_open

def reset (runid:int, tn:str, tskn, alg)->None:
    if not dawgie.db.post._db: raise RuntimeError('called reset before open')

    conn = dawgie.db.post._conn()
    cur = dawgie.db.post._cur (conn)
    cur.execute('SELECT * from Target WHERE name = %s;', [tn])
    tn_ID = _fetchone(cur,'Dataset: Could not find target ID')
    cur.execute('SELECT * from TASK WHERE name = %s;', [tskn])
    task_ID = _fetchone (cur, 'Dataset load: Could not find task ID')
    cur.execute('SELECT pk FROM Algorithm WHERE name = %s AND task_ID = %s;',
                [alg.name(), task_ID])
    alg_ID = list({pk[0] for pk in cur.fetchall()})
    algv = set()
    for sv in alg.state_vectors():
        cur.execute('SELECT pk FROM StateVector WHERE name = %s AND ' +
                    'alg_ID = ANY(%s);', [sv.name(), alg_ID])
        sv_ID = list({pk[0] for pk in cur.fetchall()})
        cur.execute('SELECT alg_ID, sv_ID FROM Prime WHERE run_ID = %s AND ' +
                    ' tn_ID = %s AND task_ID = %s AND alg_ID = ANY(%s) AND ' +
                    'sv_ID = ANY(%s);',
                    [str(runid), tn_ID, task_ID, alg_ID, sv_ID])
        ids = cur.fetchall()
        algv.update ({fk[0] for fk in ids})
        svv = {fk[1] for fk in ids}

        if len (svv) == 1:
            cur.execute ('SELECT design,implementation,bugfix '+
                         'FROM StateVector WHERE PK = %s;', [svv.pop()])
            v = cur.fetchone()
            sv._set_ver (dawgie.VERSION(v[0],v[1],v[2]))
        else: log.critical ('Dataset load: The postgres db is corrupt because found %d IDs for the specific state vector %s',
                            len (svv), '.'.join ([str (runid),
                                                  tn, tskn,
                                                  alg.name(),
                                                  sv.name()]))
        pass
    if len (algv) == 1:
        cur.execute ('SELECT design,implementation,bugfix '+
                     'FROM Algorithm WHERE PK = %s;', [algv.pop()])
        v = cur.fetchone()
        alg._set_ver (dawgie.VERSION(v[0],v[1],v[2]))
    else: log.critical ('Dataset load: The postgres db is corrupt because found %d IDs for the specific algorithm %s',
                        len (svv),
                        '.'.join ([str (runid), tn, tskn, alg.name()]))
    conn.commit()
    cur.close()
    conn.close()
    return

def retreat (reg, ret):
    if not dawgie.db.post._db: raise RuntimeError('called retreat before open')
    return Interface(reg, ret, ret._target())

def targets():
    if not dawgie.db.post._db: raise RuntimeError('called targets before open')

    log.debug ("in targets()")
    conn = _conn()
    cur = _cur (conn)
    cur.execute('SELECT name from Target;')
    result = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in result]

def trace (task_alg_names):
    if not dawgie.db.post._db: raise RuntimeError('called trace before open')

    target_list = dawgie.db.targets()
    conn = _conn()
    cur = _cur (conn)
    result = {}
    for tn in target_list:
        result[tn] = {}
        for tan in task_alg_names:
            tskn,algn = tan.split('.')
            version = []
            cur.execute ('SELECT PK FROM Target WHERE name = ANY(%s);',
                         [['__all__', tn]])
            tnids = list({pk[0] for pk in cur.fetchall()})
            cur.execute ('SELECT PK FROM Task WHERE name = %s;', [tskn])
            tid = cur.fetchone()[0]
            cur.execute ('SELECT MAX(design) ' +
                         'FROM Algorithm WHERE task_ID = %s AND name = %s;',
                         [tid, algn])
            version.extend (cur.fetchone())
            cur.execute ('SELECT MAX(implementation) ' +
                         'FROM Algorithm WHERE task_ID = %s AND name = %s ' +
                         'AND design = %s;',
                         [tid, algn] + version)
            version.extend (cur.fetchone())
            cur.execute ('SELECT MAX(bugfix) ' +
                         'FROM Algorithm WHERE task_ID = %s AND name = %s ' +
                         'AND design = %s AND implementation = %s;',
                         [tid, algn] + version)
            version.extend (cur.fetchone())
            cur.execute ('SELECT PK FROM Algorithm WHERE task_ID = %s AND ' +
                         'name = %s AND design = %s AND implementation = %s ' +
                         'AND bugfix = %s;',
                         [tid, algn] + version)
            aid = cur.fetchone()[0]
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
    if not dawgie.db.post._db: raise RuntimeError('called update before open')

    log.debug ("In databse update")
    # Just adds these things to their respective tables
    # Check if connection to DB is already open
    if not dawgie.db.post._db: raise RuntimeError('Called before open')

    conn = _conn()
    cur = _cur (conn)
    # Add stuff. Check if they already exist in the tables first.
    try:
        cur.execute ('INSERT into Task(name) values (%s);', [tsk._name()])
        conn.commit()
    except psycopg.IntegrityError: conn.rollback()
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
    except psycopg.IntegrityError: conn.rollback()

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
        except psycopg.IntegrityError: conn.rollback()
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
        except psycopg.IntegrityError: conn.rollback()
        pass

    cur.close()
    conn.close()
    return

def versions():
    # Returns Algorithm, StateVector, and Value as a list of dictionaries
    # where each dictionary represents a row in the table
    if not dawgie.db.post._db: raise RuntimeError('called versions before open')

    log.debug ('versions() - starting')
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
    log.debug ('versions() - starting')
    return task_ver, alg_ver, sv_ver, v_ver

def view_locks(): return {'msg':'<h1>Not Applicable with postgresql database',
                          'tasks':[]}
