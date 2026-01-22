'''The API to all things dawgie.pl.farm and dawgie.pl.schedule'''

from dawgie.fe.basis import Status, build_return_object

import dawgie.context
import dawgie.pl.farm
import dawgie.pl.schedule


def doing(asis: bool = False):
    if asis:
        return dawgie.pl.schedule.view_doing()
    return build_return_object(dawgie.pl.schedule.view_doing())


def failed(asis: bool = False):
    if asis:
        return dawgie.pl.schedule.view_failure()
    return build_return_object(dawgie.pl.schedule.view_failure())


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


def succeeded(asis: bool = False):
    if asis:
        return dawgie.pl.schedule.view_success()
    return build_return_object(dawgie.pl.schedule.view_success())


def todo(asis: bool = False):
    reformatted = {
        old['name']: old['targets'] for old in dawgie.pl.schedule.view_todo()
    }
    if asis:
        return reformatted
    return build_return_object(reformatted)
