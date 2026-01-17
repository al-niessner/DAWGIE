'''The API to all things dawgie.pl.farm and dawgie.pl.schedule'''

from dawgie.fe.basis import Status, build_return_object

import dawgie.context
import dawgie.pl.farm
import dawgie.pl.schedule


def stats():
    if not dawgie.context.fsm.is_pipeline_active():
        return build_return_object(
            None,
            Status.FAILURE,
            'The pipeline is not "ready". See /api/pipeline/state for more details.',
        )
    doing = sum(len(v) for v in dawgie.pl.schedule.view_doing().values())
    todo = sum(len(i['targets']) for i in dawgie.pl.schedule.view_todo())
    workers = dawgie.pl.farm.crew()
    return build_return_object(
        {
            'jobs': {'doing': doing, 'todo': todo},
            'workers': {
                'busy': len(workers['busy']),
                'idle': int(workers['idle']),
            },
        }
    )
