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
from dawgie.fe import submit
from dawgie.fe import svrender

import dawgie
import dawgie.context
import dawgie.pl.logger.fe

import logging; log = logging.getLogger(__name__)  # fmt: skip # noqa: E702 # pylint: disable=multiple-statements

from . import database
from . import schedule


def ae_name():
    return build_return_object(dawgie.context.ae_base_package)


def df_model_statistics(node_name: str):
    node_name = node_name[0]
    if not node_name:
        build_return_object(
            None, Status.FAILURE, "Node name was not given or is blank"
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
# DynamicContent(, '/api/cmd/run')
DynamicContent(database.runnables, '/api/database/runnables')
# DynamicContent(database., '/api/database/search')
# DynamicContent(database., '/api/database/search/runid')  # no params returns max value
# DynamicContent(database., '/api/database/search/target')  # no params returns full list
# DynamicContent(database., '/api/database/search/task')  # no params returns full list
# DynamicContent(database., '/api/database/search/alg')  # no params returns full list
# DynamicContent(database., '/api/database/search/sv')  # no params returns full list
# DynamicContent(database., '/api/database/search/val')  # no params returns full list
DynamicContent(database.targets, '/api/database/targets')
# DynamicContent(database., '/api/database/view')  # given a full name, generate its view
DynamicContent(df_model_statistics, '/api/df_model/statistics')
DynamicContent(logs_recent, '/api/logs/recent')
DynamicContent(pipeline_state, '/api/pipeline/state')
DynamicContent(rev_current, '/api/rev/current')
# DynamicContent(, '/api/rev/submit')
# DynamicContent(schedule., '/api/schedule/doing')
# DynamicContent(schedule., '/api/schedule/failed')
# DynamicContent(schedule., '/api/schedule/in-progress')
DynamicContent(schedule.stats, '/api/schedule/stats')
# DynamicContent(schedule., '/api/schedule/succeeded')
# DynamicContent(schedule., '/api/schedule/to-do')
