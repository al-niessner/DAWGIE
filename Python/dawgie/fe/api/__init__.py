'''Define the bits of the front end that require some help from the server

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

from dawgie.fe.basis import (
    DynamicContent,
    HttpMethod,
    Status,
    build_return_object,
)

import dawgie
import dawgie.context
import dawgie.pl.logger.fe
import logging

from . import database
from . import facet
from . import schedule
from . import submit

LOG = logging.getLogger(__name__)
REV_SUBMIT = submit.Defer()


def ae_name():
    return build_return_object(dawgie.context.ae_base_package)


def cmd_reset(archive: [str] = None):
    archive = archive[0] if archive and archive[0] else 'false'
    affirmative = ['true', 'tru', 'tr', 't', 'y', 'ye', 'yes', 'on']
    archive = archive.lower() in affirmative
    if not hasattr(dawgie.context, 'fsm'):
        return build_return_object(
            None, Status.FAILURE, 'Resetting before FSM is defined.'
        )
    if not dawgie.context.fsm.is_pipeline_active():
        return build_return_object(
            None, Status.FAILURE, 'Cannot reset a pipeline that is not active.'
        )
    LOG.critical('User requested pipeline reset')
    dawgie.pl.farm.ARCHIVE |= archive
    dawgie.context.fsm.wait_for_nothing()
    return build_return_object('Reset the pipeline as requested.')


def cmd_run(runnables: [str], targets: [str]):
    dawgie.pl.schedule.organize(
        task_names=set(runnables),
        targets=set(targets),
        event='command-run requested by user',
    )
    return build_return_object('Scheduled target.task(s) to run.')


def cmd_snapshot():
    return build_return_object(dawgie.pl.snapshot.grab())


def df_model_statistics(node_name: str):
    node_name = node_name[0]
    if not node_name:
        build_return_object(
            None, Status.FAILURE, 'Node name was not given or is blank'
        )
    if node_name.count('.') > 1:
        node_name = '.'.join(node_name.split('.')[:2])
    if node_name in schedule.doing(True):
        return build_return_object({'status': 'processing'})
    if node_name in schedule.todo(True):
        return build_return_object({'status': 'scheduled'})
    matched = []
    for known in schedule.failed(True):
        if known['task'] == node_name:
            known['status'] = 'failed'
            matched.append(known)
    for known in schedule.succeeded(True):
        if known['task'] == node_name:
            known['status'] = 'succeeded'
            matched.append(known)
    if not matched:
        return build_return_object({})
    runid = max(m['runid'] for m in matched)
    matched = list(filter(lambda d, rid=runid: d['runid'] == rid, matched))
    status = set(m['status'] for m in matched)
    if len(status) > 1:
        status = 'both'
    else:
        status = status.pop()
    matched.sort(key=lambda d: d['timing']['completed'], reverse=True)
    return build_return_object(
        {
            'date': matched[0]['timing']['completed'],
            'runid': matched[0]['runid'],
            'status': status,
        }
    )


def logs_recent(levels: [str] = None, limit: [int] = None):
    if levels:
        levels = [level.upper() for level in levels[0].split(',')]
    else:
        levels = ['WARNING', 'ERROR', 'CRITICAL']
    if limit:
        limit = int(limit[0])
    else:
        limit = 0
    return build_return_object(dawgie.pl.logger.fe.remembered(levels, limit))


def pipeline_state():
    return build_return_object(
        {
            'name': dawgie.context.fsm.state,
            'ready': dawgie.context.fsm.is_pipeline_active(),
            'status': dawgie.context.fsm.transitioning.name,
        }
    )


def rev_current():
    return build_return_object(dawgie.context.git_rev)


DynamicContent(ae_name, '/api/ae/name')
DynamicContent(cmd_reset, '/api/cmd/reset', [HttpMethod.POST])
DynamicContent(cmd_run, '/api/cmd/run', [HttpMethod.POST])
DynamicContent(cmd_snapshot, '/api/cmd/snapshot')
DynamicContent(facet.target, '/api/database/filter/target')
DynamicContent(facet.task, '/api/database/filter/task')
DynamicContent(facet.alg, '/api/database/filter/alg')
DynamicContent(facet.sv, '/api/database/filter/sv')
DynamicContent(database.runid_max, '/api/database/runid/max')
DynamicContent(database.runnables, '/api/database/runnables')
DynamicContent(database.search, '/api/database/search')
DynamicContent(database.list_targets, '/api/database/targets')
DynamicContent(database.VIEW, '/api/database/view')
DynamicContent(df_model_statistics, '/api/df_model/statistics')
DynamicContent(logs_recent, '/api/logs/recent')
DynamicContent(pipeline_state, '/api/pipeline/state')
DynamicContent(rev_current, '/api/rev/current')
DynamicContent(REV_SUBMIT, '/api/rev/submit', [HttpMethod.POST])
DynamicContent(schedule.doing, '/api/schedule/doing')
DynamicContent(schedule.events, '/api/schedule/events')
DynamicContent(schedule.failed, '/api/schedule/failed')
DynamicContent(schedule.inprogress, '/api/schedule/in-progress')
DynamicContent(schedule.stats, '/api/schedule/stats')
DynamicContent(schedule.succeeded, '/api/schedule/succeeded')
DynamicContent(schedule.todo, '/api/schedule/to-do')
