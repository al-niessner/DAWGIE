'''take a snapshot of the running pipeline state

The snapshot state is incomplete and can be changes as necessary to support live debugging. It was added for issue_206 because there is an intermitten behavior of the pipeline where the farm has work to do, idle hands to do the work, but nothinng is moving to the workers. The description of 206 shows that it is the _busy and _cluster lists seem to be cleared while do and doing in the tasks themselves are not empty. It puts the problem squarely in the farm but without knowing its internal state, it is not possible to determine the cause let alone root cause of the erroneous behavior.

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

import dawgie.context
import dawgie.pl.farm
import dawgie.pl.message
import dawgie.pl.schedule
import gc
import resource
import sys

# snapshoting requires peeking so pylint: disable=protected-access


def _clean(item):
    if isinstance(item, dawgie.pl.message.MSG):
        return dawgie.pl.message.make(
            fac=item.factory,
            inc=item.incarnation,
            jid=item.jobid,
            psh=item.ps_hint,
            rev=item.revision,
            rid=item.runid,
            suc=item.success,
            target=item.target,
            tim=item.timing,
            typ=item.type,
            val=item.values,
        )
    return item


def _grab_context():
    if ':' in dawgie.context.db_path:
        dbp = (
            dawgie.context.db_path[: dawgie.context.db_path.find(':')] + ':****'
        )
    else:
        dbp = dawgie.context.db_path
    return {
        'context': {
            'ae_base_path': dawgie.context.ae_base_path,
            'ae_base_package': dawgie.context.ae_base_package,
            'allow_promotion': dawgie.context.allow_promotion,
            'cloud_data': dawgie.context.cloud_data,
            'cloud_port': dawgie.context.cloud_port,
            'cloud_provider': str(dawgie.context.cloud_provider),
            'cpu_threshold': dawgie.context.cpu_threshold,
            'data_dbs': dawgie.context.data_dbs,
            'data_log': dawgie.context.data_log,
            'data_stg': dawgie.context.data_stg,
            'db_host': dawgie.context.db_host,
            'db_impl': dawgie.context.db_impl,
            'db_name': dawgie.context.db_name,
            'db_path': dbp,
            'db_port': dawgie.context.db_port,
            'display': str(dawgie.context.display),
            'farm_port': dawgie.context.farm_port,
            'fe_path': dawgie.context.fe_path,
            'fe_port': dawgie.context.fe_port,
            'git_rev': str(dawgie.context.git_rev),
            'guest_public_keys': dawgie.context.guest_public_keys,
            'log_level': dawgie.context.log_level,
            'log_port': dawgie.context.log_port,
            'worker_backlog': dawgie.context.worker_backlog,
        }
    }


def _grab_farm():
    return {
        'farm': {
            'agency': str(dawgie.pl.farm._agency),
            'busy': [str(_clean(b)) for b in dawgie.pl.farm._busy],
            'cloud': [str(_clean(c)) for c in dawgie.pl.farm._cloud],
            'cluster': [str(_clean(c)) for c in dawgie.pl.farm._cluster],
            'crew': dawgie.pl.farm.crew(),
            'something_to_do': dawgie.pl.farm.something_to_do(),
            'time': {str(k): str(t) for k, t in dawgie.pl.farm._time.items()},
            'workers': [str(b) for b in dawgie.pl.farm._workers],
        }
    }


def _grab_fsm():
    if dawgie.context.fsm is None:
        return {'fsm': 'None'}
    return {
        'fsm': {
            'state': dawgie.context.fsm.state,
            'waiting_on_crew': dawgie.context.fsm.waiting_on_crew(),
            'waiting_on_doing': dawgie.context.fsm.waiting_on_doing(),
            'waiting_on_todo': dawgie.context.fsm.waiting_on_todo(),
        }
    }


def _grab_memory():
    gcnt = -1
    gsize = -1
    nodes = []
    objs_id = -1
    try:
        gc.disable()
        gc.collect()
        objs = gc.get_objects()
        objs_id = hex(id(objs))
        gcnt = len(gc.garbage)
        gsize = sum(sys.getsizeof(obj) for obj in gc.garbage)
        gc.collect()
        for obj in objs:
            refs = gc.get_referents(obj)
            nodes.append(
                {
                    'obj': {
                        'id': hex(id(obj)),
                        'size': sys.getsizeof(obj),
                        'type': str(type(obj)),
                    },
                    'refs': [hex(id(ref)) for ref in refs],
                }
            )
            pass
    finally:
        gc.enable()
    return {
        'garbage': {'count': gcnt, 'size': gsize},
        'nodes': nodes,
        'objs_id': objs_id,
    }


def _grab_res(who):
    ru = resource.getrusage(who)
    return {
        attrname: getattr(ru, attrname)
        for attrname in filter(lambda s: s.startswith('ru_'), dir(ru))
    }


def _grab_schedule():
    return {
        'schedule': {
            'doing': dawgie.pl.schedule.view_doing(),
            'events': dawgie.pl.schedule.view_events(),
            'todo': dawgie.pl.schedule.view_todo(),
        }
    }


def grab(which: str = 'all') -> {}:
    result = {}
    if 'all' in which or 'context' in which:
        result.update(_grab_context())
    if 'all' in which or 'farm' in which:
        result.update(_grab_farm())
    if 'all' in which or 'fsm' in which:
        result.update(_grab_fsm())
    if 'all' in which or 'memory' in which:
        result.update(_grab_memory())
    if 'all' in which or 'resources' in which:
        result.update(
            {
                'resources': {
                    'self': _grab_res(resource.RUSAGE_SELF),
                    'children': _grab_res(resource.RUSAGE_CHILDREN),
                }
            }
        )
    if 'all' in which or 'schedule' in which:
        result.update(_grab_schedule())
    return result
