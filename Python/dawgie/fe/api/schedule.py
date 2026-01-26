'''The API to all things dawgie.pl.farm and dawgie.pl.schedule'''

from dawgie.fe.basis import Status, build_return_object

import dawgie.context
import dawgie.pl.farm
import dawgie.pl.schedule


def _legacy_arg_fixer(index: int, limit: int):
    if index is None:
        index = 0
    if isinstance(index, list):
        index = index[0]
    index = int(index)
    if isinstance(limit, list) and limit:
        limit = limit[0]
    try:
        limit = int(limit)
    except TypeError:
        limit = None
    return index, limit, (index + limit) if limit is not None else limit


def doing(asis: bool = False, index: int = 0, limit: int = None):
    if asis:
        return dawgie.pl.schedule.view_doing(index, limit)
    index, limit = _legacy_arg_fixer(index, limit)[:2]
    return build_return_object(dawgie.pl.schedule.view_doing(index, limit))


def events(index: int = 0, limit: int = None):
    index, _limit, term = _legacy_arg_fixer(index, limit)
    e = {
        d['actor']: d['delays']
        for d in dawgie.pl.schedule.view_events()[index:term]
    }
    return build_return_object(e)


def failed(asis: bool = False, index: int = 0, limit: int = None):
    if asis:
        return dawgie.pl.schedule.view_failure()
    f = dawgie.pl.schedule.view_failure()
    f.reverse()
    index, _limit, term = _legacy_arg_fixer(index, limit)
    return build_return_object(f[index:term])


def inprogress(index: int = 0, limit: int = None):
    index, _limit, term = _legacy_arg_fixer(index, limit)
    return build_return_object(dawgie.pl.farm.crew()['busy'][index:term])


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
    index, _limit, term = _legacy_arg_fixer(index, limit)
    s = dawgie.pl.schedule.view_success()
    s.reverse()
    return build_return_object(s[index:term])


def todo(asis: bool = False, index: int = 0, limit: int = None):
    index, limit = _legacy_arg_fixer(index, limit)[:2]
    reformatted = {
        old['name']: old['targets']
        for old in dawgie.pl.schedule.view_todo(index, limit)
    }
    if asis:
        return reformatted
    return build_return_object(reformatted)
