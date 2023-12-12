'''Define the bits of the front end that require some help from the server

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

from dawgie.fe import DynamicContent, HttpMethod
from . import submit
from . import svrender

import dawgie
import dawgie.context
import dawgie.db
import dawgie.de
import dawgie.pl.farm
import dawgie.pl.logger.fe
import dawgie.pl.schedule
import dawgie.pl.snapshot
import enum
import json
import logging; log = logging.getLogger(__name__)
import pkg_resources
import os
import sys

class Axis(enum.Enum):
    runid = 0
    svn = 1
    tn = 2
    pass

def db_lockview():
    return json.dumps(dawgie.db.view_locks()).encode()

def db_prime():
    # pylint: disable=protected-access
    return json.dumps (list({'.'.join (k.split ('.')[:-1])
                                 for k in dawgie.db._prime_keys()})).encode()

def db_targets():
    return json.dumps (dawgie.db.targets(True)).encode()

def db_versions():
    return json.dumps (dawgie.db.versions()).encode()

def log_messages():
    return json.dumps (dawgie.pl.logger.fe.remembered()).encode()

def pl_state():
    return json.dumps ({'name':dawgie.context.fsm.state,
                        'status':'active'}).encode()

def schedule_crew():
    return json.dumps (dawgie.pl.farm.crew()).encode()

def schedule_doing():
    return json.dumps (dawgie.pl.schedule.view_doing()).encode()

def schedule_events():
    return json.dumps (dawgie.pl.schedule.view_events()).encode()

def schedule_failure():
    return json.dumps (dawgie.pl.schedule.view_failure()).encode()

def schedule_run (tasks:[str], targets:[str]):
    log.debug ('schedule_run: targets %s', str(targets))
    log.debug ('schedule_run: tasks %s', str(tasks))
    dawgie.pl.schedule.organize (task_names=tasks,
                                 targets=set(targets),
                                 event='command-run requested by user')
    return json.dumps ({'alert_status':'success',
                        'alert_message':'All jobs scheduled to run.'}).encode()

def schedule_success():
    return json.dumps (dawgie.pl.schedule.view_success()).encode()

def schedule_tasks():
    return json.dumps (dawgie.pl.schedule.tasks()).encode()

def schedule_todo():
    return json.dumps (dawgie.pl.schedule.view_todo()).encode()

def snapshot():
    return json.dumps (dawgie.pl.snapshot.grab()).encode()

def _s0 (k): return k.split('.')[0]
def _s1 (k): return k.split('.')[1]
def _s2 (k): return '.'.join (k.split('.')[2:])
def _search (axis, key):
    # pylint: disable=cell-var-from-loop,protected-access
    if axis == Axis.runid:
        k1,k2,k3,k4 = 'run_id', 'targets', 'target_name', 'state_vectors'
        prime,second,third = _s0,_s1,_s2
        pass
    if axis == Axis.svn:
        k1,k2,k3,k4 = 'state_vector', 'targets', 'name', 'ids'
        prime,second,third = _s2,_s1,_s0
        pass
    if axis == Axis.tn:
        k1,k2,k3,k4 = 'target_name', 'targets', 'state_vector', 'ids'
        prime,second,third = _s1,_s2,_s0
        pass

    result = {'items':[]}
    keys = list({'.'.join (k.split ('.')[:-1])
                 for k in filter (lambda k:-1 < prime(k).find (key),
                                  dawgie.db._prime_keys())})
    keys.sort (key=prime)
    for lkey in sorted ({prime (k) for k in keys}):
        result['items'].append ({k1:lkey, k2:[]})
        tnks = list(filter (lambda k:prime (k) == lkey, keys))
        for nn in sorted ({second (k) for k in tnks}):
            ids = sorted ({third (k) for k in
                           filter (lambda k:second (k) == nn, tnks)})
            result['items'][-1]['targets'].append ({k3:nn, k4:ids})
            pass
        pass
    return json.dumps (result).encode()

def _search_filter (fn:str, default:{})->bytes:
    if os.path.isfile (os.path.join (dawgie.context.fe_path, fn)):
        try:
            with open (os.path.join (dawgie.context.fe_path, fn),
                       'rt', encoding="utf-8") as f: default = json.load(f)
        except: log.exception ('Text file could not be parsed as JSON')  # pylint: disable=bare-except
    else: log.debug ('using DAWGIE default for %s', fn)
    return json.dumps (default).encode()

def search_cmplt_svn():
    # pylint: disable=protected-access
    return json.dumps(sorted({'.'.join (k.split('.')[2:-1])
                              for k in dawgie.db._prime_keys()})).encode()
def search_cmplt_tn(): return json.dumps(sorted(dawgie.db.targets())).encode()

def search_filter_a(): return _search_filter ('admin.json',
                                              {'include':{'.__metric__$':[]}})
def search_filter_d(): return _search_filter ('dev.json',
                                              {'exclude':{'.__metric__$':[]}})
def search_filter_u(): return _search_filter ('user.json',
                                              {'exclude':{'.__metric__$':[]}})

# pylint: disable=dangerous-default-value
def search_runid(key:[str]=['']): return _search (Axis.runid, key[0])
def search_svn(key:[str]=['']): return _search (Axis.svn, key[0])
def search_tn(key:[str]=['']): return _search (Axis.tn, key[0])

def start_changeset():
    return dawgie.context.git_rev.encode('utf-8')

def start_state():
    return json.dumps ({'name':dawgie.context.fsm.state,
                        'status':'active'}).encode()

def versions():
    # it is iterable so pylint: disable=not-an-iterable
    dl = {p.key:p.parsed_version.base_version for p in pkg_resources.working_set}
    # pylint: enable=not-an-iterable
    fn = os.path.join (os.path.dirname (__file__), 'requirements.txt')
    vers = {'dawgie':dawgie.__version__,
            'python':sys.version}
    with open (fn, 'rt', encoding="utf-8") as f:
        for name in f.readlines():
            if name in dl: vers[name] = dl[name]
            else: vers[name] = 'indeterminate'
            pass
        pass
    return json.dumps (vers).encode()

start_submit = submit.Defer()
sv_renderer = svrender.Defer()

DynamicContent(sv_renderer, '/app/db/item')
DynamicContent(db_lockview, '/app/db/lockview')
DynamicContent(db_prime, '/app/db/prime')
DynamicContent(db_targets, '/app/db/targets')
DynamicContent(db_versions, '/app/db/versions')

DynamicContent(log_messages, '/app/pl/log')

DynamicContent(pl_state, '/app/pl/state')

DynamicContent(schedule_crew, '/app/schedule/crew')
DynamicContent(schedule_doing, '/app/schedule/doing')
DynamicContent(schedule_events, '/app/schedule/events')
DynamicContent(schedule_failure, '/app/schedule/failure')
DynamicContent(schedule_run, '/app/run', [HttpMethod.POST])
DynamicContent(schedule_success, '/app/schedule/success')
DynamicContent(schedule_tasks, '/app/schedule/tasks')
DynamicContent(schedule_todo, '/app/schedule/todo')

DynamicContent(search_cmplt_svn, '/app/search/completion/sv')
DynamicContent(search_cmplt_tn, '/app/search/completion/tn')
DynamicContent(search_filter_a, '/app/filter/admin')
DynamicContent(search_filter_d, '/app/filter/dev')
DynamicContent(search_filter_u, '/app/filter/user')
DynamicContent(search_runid, '/app/search/ri')
DynamicContent(search_svn, '/app/search/sv')
DynamicContent(search_tn, '/app/search/tn')

DynamicContent(start_changeset, '/app/changeset.txt')
DynamicContent(snapshot, '/app/snapshot')
DynamicContent(start_state, '/app/state/status')
DynamicContent(start_submit, '/app/submit', [HttpMethod.POST])
DynamicContent(versions, '/app/versions')
