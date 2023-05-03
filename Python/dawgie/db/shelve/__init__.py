'''A shelve database implementation

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

import dawgie.context
import dawgie.db
import dawgie.db.util
import logging; log = logging.getLogger(__name__)
import os

from . import util
from .comms import Connector
from .comms import DBSerializer
from .enums import Method
from .enums import Table
from .model import Interface
from .state import DBI

def _prime_keys()->[(int,str,str,str,str,str)]:
    if not DBI().is_open: raise RuntimeError('called _prime_keys before open')
    return ['.'.join ([str(key[0]),
                       util.dissect(DBI().indices.target[key[1]])[1],
                       util.dissect(DBI().indices.task[key[2]])[1],
                       util.dissect(DBI().indices.alg[key[3]])[1],
                       util.dissect(DBI().indices.state[key[4]])[1],
                       util.dissect(DBI().indices.value[key[5]])[1]])
            for key in util.prime_keys(DBI().tables.prime)]

def _prime_values()->[str]:
    if not DBI().is_open:
        raise RuntimeError('called _prime_keys before open')
    return list(DBI().tables.prime.values())

def add (target_name:str)->bool:
    '''Add a new target to the known list

    target_name - the name of the target to add

    return True if the target already exists or was successfully added and
           False otherwise
    '''
    if DBI().is_reopened:
        result = Connector().set (target_name, None, Table.target, None, None)
    elif DBI().is_open:
        result = util.append (target_name,
                              DBI().tables.target, DBI().indices.target)
    else: raise RuntimeError('called add before open')
    return result[0]

def archive (done):
    '''Archive the current state of the database'''
    if DBI().is_reopened:
        raise RuntimeError('archive should only be called from the ' +
                           'pipeline Foreman context')

    path = dawgie.context.db_rotate_path
    if not (os.path.exists (path) and os.path.isdir (path)):
        raise ValueError('The path "' + path +
                         '" does not exist or is not a directory')

    if DBI().is_open:
        reconnect = True
        log.critical ('called _rotate after open')
        DBI().close()
    else: reconnect = False

    orig = util.rotated_files()
    backup = {}
    for i in range(dawgie.context.db_rotate):
        backup[i] = util.rotated_files(i)
        pass
    dawgie.db.util.rotate(path, orig, backup)
    overflowNum = len(backup)
    orig = util.rotated_files(overflowNum)
    for e in orig: os.remove(e)

    if reconnect: open()

    done()
    return


def close():
    '''Close the database'''
    DBI().close()
    return

def connect (alg, bot, tn)->dawgie.Dataset:
    '''Connect an dawgie.Dataset to the database backend

    Separates the user from the database implementation.

    alg - the instance of dawgie.Algorithm that will be using the Dataset
    bot - the instance of dawgie.Task that will be calling alg
    tn  - the target name
    '''
    if not DBI().is_open: raise RuntimeError('called connect before open')
    return Interface(alg, bot, tn)

def consistent (inputs:[dawgie.db.REF],
                outputs:[dawgie.db.REF],
                target_name:str)->():
    '''Find self consistent inputs for the output returning base table entry

    REF - tid is Analysis/Regress/Task dawgie.db.ID (use None for version)
        - aid is Algorithm/Analyzer/Regression dawgie.db.ID
        - sid is StateVector dawgie.db.ID
        - vid is Value dawgie.db.ID

    inputs  - list of consistent inputs to find
    outputs - consistent for these outputs
    target_name - which target

    returns a tuple that can be used by dawgie.db.promote to create a new entry
            in the database that represents the same solution as if the AE
            were run given the inputs as it was already done. Returns an empty
            tuple or None if a consistent set of data could not be found.
    '''
    raise NotImplementedError('Not ready for shelve')

def copy (dst, method, gateway):
    '''Copy database to destination.'''
    if not DBI().is_open: raise RuntimeError('called copy before open')

    connection = Connector()
    retValue = connection.copy(dst, method)

    if method == Method.connector:
        DBI.save_as (retValue, os.path.join (dst, dawgie.context.db_name))
        status = 0
    elif method == Method.rsync:
        status = os.system(f"rsync --delete -ax {gateway}:{retValue}/ {dst}/")
    elif method == Method.scp:
        status = os.system(f"scp -rp {gateway}:{retValue}/* {dst}/")
    elif method == Method.cp: status = os.system(f"cp -rp {retValue}/* {dst}/")

    return status

def gather (anz, ans)->dawgie.Aspect:
    '''Gather an dawgie.Aspect to the database backend

    anz : instance of dawgie.Analyzer that will be using the Aspect
    ans : instance of dawgie.Analysis that creates the anz
    '''
    if not DBI().is_open: raise RuntimeError('called connect before open')
    return Interface(anz, ans, '__all__')


def metrics()->[dawgie.db.METRIC_DATA]:
    if not DBI().is_open: raise RuntimeError('called metrics before open')
    if DBI().is_reopened: raise RuntimeError('called outside of Foremen context')

    result = []
    log.debug ('metrics() - starting')
    keys = util.prime_keys(DBI().tables.prime)
    log.debug ('metrics() - total prime keys %d', len (keys))
    mkeys = {}
    for k in filter (lambda k:'__metric__' in k, DBI().tables.state):
        name = k[:k.rfind(':')]
        if name not in mkeys: mkeys[name] = []
        mkeys[name].append (k)
        pass
    mkeys = [sorted(mk, key=lambda k:util.dissect(k)[2])[-1]
             for mk in mkeys.values()]
    akeys = {}
    for k in mkeys:
        k = DBI().indices.alg[util.dissect (k)[0]]
        name = k[:k.rfind(':')]
        if name not in akeys: akeys[name] = []
        akeys[name].append (k)
        pass
    akeys = [DBI().tables.alg[sorted(ak, key=lambda k:util.dissect(k)[2])[-1]]
             for ak in akeys.values()]
    mkeys = [DBI().tables.state[mk]
             for mk in filter (lambda k,K=akeys:util.dissect(k)[0] in K, mkeys)]
    keys = list(filter(lambda k,K=mkeys:k[4] in K, keys))
    log.debug ('metrics() - total __metric__ in prime keys %d', len (keys))
    for m in sorted(keys):
        runid = int(m[0])
        target = util.dissect(DBI().indices.target[m[1]])[1]
        task = util.dissect(DBI().indices.task[m[2]])[1]
        alg = util.dissect(DBI().indices.alg[m[3]])[1:]
        sv = util.dissect(DBI().indices.state[m[4]])[1:]
        val = util.dissect(DBI().indices.value[m[5]])[1:]
        mn = '.'.join ([str(runid), target, task, alg[0], sv[0], val[0]])
        log.debug ('metrics() - working on %s', mn)

        if not result or any ([result[-1].run_id != runid,
                               result[-1].target != target,
                               result[-1].task != task,
                               result[-1].alg_name != alg[0],
                               result[-1].alg_ver != alg[1].version]):
            log.debug ('metrics() - make new reuslt')
            msv = dawgie.util.MetricStateVector(dawgie.METRIC(-2,-2,-2,-2,-2,-2),
                                                dawgie.METRIC(-2,-2,-2,-2,-2,-2))
            result.append (dawgie.db.METRIC_DATA(alg_name=alg[0],
                                                 alg_ver=alg[1].version,
                                                 run_id=runid, sv=msv,
                                                 target=target, task=task))
            log.debug ('metrics() - result length %d', len (result))
            pass

        try:
            log.debug ('metrics() - reading data and decoding')
            msv[val[0]] = dawgie.db.util.decode (DBI().tables.prime[str(m)])
        except FileNotFoundError: log.exception('missing metric data for %s',mn)
        pass
    return result

def next():  # pylint: disable=redefined-builtin
    '''Return the next run ID'''
    if not DBI().is_open: raise RuntimeError('called next before open')
    if DBI().is_reopened: raise RuntimeError('called outside of Foreman context')

    known = [int(key[0]) for key in util.prime_keys (DBI().tables.prime)]
    return max(known)+1 if known else 1

def open():  # pylint: disable=redefined-builtin
    '''Open the database'''
    if not os.path.isdir (dawgie.context.db_path):
        raise ValueError(f'The path "{dawgie.context.db_path}" ' +
                         'does not exist or is not a directory')

    DBI().open()
    DBSerializer.open()
    return

def promote (juncture:(), runid:int):
    '''Promote the junctures to the given runid

    juncture : a list of results from dawgie.db.consistent

    retuns the full value names promoted as
    runid.target name.task name.alg name.state vector name.value name'''
    raise NotImplementedError('Not ready for shelve')

# pylint: disable=too-many-arguments,too-many-locals
def remove(runid:int, tn:str, taskn:str, algn:str, svn:str, vn:str):
    '''Remove the specified key from the prime table'''
    if not DBI().is_open: raise RuntimeError('called next before open')
    if DBI().is_reopened: raise RuntimeError('called outside of Foreman context')

    tnid = DBI().tables.target[tn]
    tskid = DBI().tables.task[taskn]
    algids = list(util.subset (DBI().tables.alg, algn, [tskid]).values())
    svids = list(util.subset (DBI().tables.state, svn, algids).values())
    vids = list(util.subset (DBI().tables.value, vn, svids).values())
    prime = DBI().tables.prime
    for algid in algids:
        for svid in svids:
            for vid in vids:
                key = str((runid, tnid, tskid, algid, svid, vid))
                if key in prime: del prime[key]
                pass
            pass
        pass
    return
# pylint: enable=too-many-arguments,too-many-locals

def reopen()->bool:
    '''open an already open database

    Used by modules outside of the pipeline but still wish to access the
    data contained within the database. When a reopen is closed, the pipeline
    will keep the database open for its own use.

    returns True if the data was open from open() already or False otherwise
    '''
    return DBI().reopen()

def retreat (reg, ret)->dawgie.Timeline:
    '''Get a dawgie.Timeline from the database backend

    reg : instance of dawgie.Regression that will be using the Timeline
    ret : instance of dawgie.Regress that creates the ret
    '''
    if not DBI().is_open: raise RuntimeError('called connect before open')
    return Interface(reg, ret, ret._target())  # pylint: disable=protected-access

def targets():
    if not DBI().is_open: raise RuntimeError('called next before open')
    return (Connector().keys (Table.target) if DBI().is_reopened else
            list(DBI().tables.target))


def trace (task_alg_names:[str])->{str:{str:int}}:
    '''trace the task_alg_names to find the lastest runid for each target

    returns {target_name:{task_alg_name:runid}}
    '''
    if not DBI().is_open: raise RuntimeError('called next before open')
    if DBI().is_reopened: raise RuntimeError('called outside of Foreman context')

    result = {}
    subprime = {}
    for runid,tid,tskid,algid,_svid,_vid in util.prime_keys(DBI().tables.prime):
        subkey = (tid,tskid,algid)
        if subkey in subprime: subprime[subkey].append (runid)
        else: subprime[subkey] = [runid]
        pass
    for subkey,runids in subprime.items(): subprime[subkey] = max(runids)
    for tn in dawgie.db.targets():
        result[tn] = {}
        tid = DBI().tables.target[tn]
        for tan in task_alg_names:
            taskn,algn = tan.split('.')
            tskid = DBI().tables.task[taskn]
            algid = DBI().tables.alg[sorted (list(util.subset (DBI().tables.alg,
                                                               algn, [tskid])),
                                             key=lambda id:util.dissect(id)[2])[-1]]
            subkey = (tid,tskid,algid)
            if subkey in subprime: result[tn][tan] = subprime[subkey]
            elif '__all__' in DBI().tables.target:
                subkey = (DBI().tables.target['__all__'],tskid,algid)
                if subkey in subprime: result[tn][tan] = subprime[subkey]
                pass
            pass
        pass
    return result

def update (tsk, alg, sv, vn, v):
    '''Update the database with version information

    updates all elements if current version is not in the database (slow)

    tsk
    alg - instance of dawgie.Algorithm
    sv  - instance of dawgie.StateVector
    vn  - value name
    v   - instance of dawgie.Value
    '''
    if not DBI().is_open: raise RuntimeError('called next before open')
    if DBI().is_reopened: raise RuntimeError('called outside of Foreman context')

    tskid = util.append (tsk._name(),  # pylint: disable=protected-access
                         DBI().tables.task, DBI().indices.task)[1]
    algid = util.append (alg.name(), DBI().tables.alg, DBI().indices.alg,
                         tskid, alg)[1]
    svid = util.append (sv.name(), DBI().tables.state, DBI().indices.state,
                        algid, sv)[1]
    util.append (vn, DBI().tables.value, DBI().indices.value, svid, v)
    return

def versions():
    '''Collate all of the known versions

    Returns alg, sv, and v dictionaries that are name:[versions as string].
    '''
    if not DBI().is_open: raise RuntimeError('called next before open')
    if DBI().is_reopened: raise RuntimeError('called outside of Foreman context')

    algs_vers = {}
    svs_vers = {}
    tasks_vers = {}
    vals_vers = {}
    for vk,pid in DBI().tables.value:
        pid,vn,vv = util.dissect (vk)
        pid,svn,svv = util.dissect (DBI().indices.state[pid])
        pid,algn,algv = util.dissect (DBI().indices.alg[pid])
        pid,tskn,_tskv = util.dissect (DBI().indices.task[pid])
        tasks_vers[tskn] = True
        key = '.'.join([tskn, algn])

        if key in algs_vers: algs_vers[key].add (algv.asstring())
        else: algs_vers[key] = {algv.asstring()}

        key = '.'.join([tskn, algn, svn])

        if key in svs_vers: svs_vers[key].add (svv.asstring())
        else: svs_vers[key] = {svv.asstring()}

        key = '.'.join([tskn, algn, svn, vn])

        if key in vals_vers: vals_vers[key].add (vv.asstring())
        else: vals_vers[key] = {vv.asstring()}
        pass
    return tasks_vers,algs_vers,svs_vers,vals_vers

def view_locks(): return DBI().task_engine.view_progress()
