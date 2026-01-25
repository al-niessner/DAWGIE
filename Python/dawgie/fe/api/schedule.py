'''The API to all things dawgie.pl.farm and dawgie.pl.schedule'''

from dawgie.fe.basis import Status, build_return_object

import dawgie.context
import dawgie.pl.farm
import dawgie.pl.schedule


def doing(asis: bool = False, index: int = 0, limit: int = None):
    if asis:
        return dawgie.pl.schedule.view_doing(index, limit)
    index = int(index[0])
    limit = limit[0] if limit else None
    limit = (int(limit) + index) if limit else None
    return build_return_object(dawgie.pl.schedule.view_doing(index, limit))


def failed(asis: bool = False, index: int = 0, limit: int = None):
    if asis:
        return dawgie.pl.schedule.view_failure()
    f = dawgie.pl.schedule.view_failure()
    index = int(index[0])
    limit = limit[0] if limit else None
    limit = (int(limit) + index) if limit else None
    return build_return_object(f[index:limit])


def inprogress(index: int = 0, limit: int = None):
    index = int(index[0])
    limit = limit[0] if limit else None
    limit = (int(limit) + index) if limit else None
    return build_return_object(dawgie.pl.farm.crew()['busy'][index:limit])


def stats():
    if not dawgie.context.fsm.is_pipeline_active():
        return build_return_object(
            None,
            Status.FAILURE,
            'The pipeline is not "ready". See /api/pipeline/state for more details.',
        )
    doing_count = sum(len(v) for v in dawgie.pl.schedule.view_doing().values())
    todo_count = sum(len(i['targets']) for i in dawgie.pl.schedule.view_todo())
    workers = dawgie.pl.farm.crew()
    return build_return_object(
        {
            'jobs': {'doing': doing_count, 'todo': todo_count},
            'workers': {
                'busy': len(workers['busy']),
                'idle': int(workers['idle']),
            },
        }
    )


def succeeded(asis: bool = False, index: int = 0, limit: int = None):
    if asis:
        return dawgie.pl.schedule.view_success()
    index = int(index[0])
    limit = limit[0] if limit else None
    limit = (int(limit) + index) if limit else None
    s = dawgie.pl.schedule.view_success()
    s.reverse()
    return build_return_object(s[index:limit])


def todo(asis: bool = False, index: int = 0, limit: int = None):
    if not asis:
        index = int(index[0])
        limit = limit[0] if limit else None
        limit = (int(limit) + index) if limit else None
    reformatted = {
        old['name']: old['targets']
        for old in dawgie.pl.schedule.view_todo(index, limit)
    }
    if asis:
        return reformatted
    return build_return_object(reformatted)
