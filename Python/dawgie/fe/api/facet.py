'''the methods to facet/filter given user constrants'''

import dawgie.db

from dawgie.db.basis import Params
from dawgie.fe.basis import build_return_object, db_param_convert


def alg(
    runids: [str] = None,
    targets: [str] = None,
    tasks: [str] = None,
    svs: [str] = None,
):
    '''facet the algorithm name

    All parameters must be a string or list with content or None. An empty list
    will cause an error in later processing.
    '''
    # pylint: disable=duplicate-code
    engine = dawgie.db.search()
    parameters = Params(
        runids=runids[0] if runids and runids[0] else None,
        targets=db_param_convert(targets),
        tasks=db_param_convert(tasks),
        algs=[],
        svs=db_param_convert(svs),
        vals=None,
    )
    return build_return_object(engine.facet(parameters))


def sv(
    runids: [str] = None,
    targets: [str] = None,
    tasks: [str] = None,
    algs: [str] = None,
):
    '''facet the state vector name

    All parameters must be a string or list with content or None. An empty list
    will cause an error in later processing.
    '''
    # pylint: disable=duplicate-code
    engine = dawgie.db.search()
    parameters = Params(
        runids=runids[0] if runids and runids[0] else None,
        targets=db_param_convert(targets),
        tasks=db_param_convert(tasks),
        algs=db_param_convert(algs),
        svs=[],
        vals=None,
    )
    return build_return_object(engine.facet(parameters))


def task(
    runids: [str] = None,
    targets: [str] = None,
    algs: [str] = None,
    svs: [str] = None,
):
    '''facet the task name

    All parameters must be a string or list with content or None. An empty list
    will cause an error in later processing.
    '''
    # pylint: disable=duplicate-code
    engine = dawgie.db.search()
    parameters = Params(
        runids=runids[0] if runids and runids[0] else None,
        targets=db_param_convert(targets),
        tasks=[],
        algs=db_param_convert(algs),
        svs=db_param_convert(svs),
        vals=None,
    )
    return build_return_object(engine.facet(parameters))


def target(
    runids: [str] = None,
    tasks: [str] = None,
    algs: [str] = None,
    svs: [str] = None,
):
    '''facet the target name

    All parameters must be a string or list with content or None. An empty list
    will cause an error in later processing.
    '''
    # pylint: disable=duplicate-code
    engine = dawgie.db.search()
    parameters = Params(
        runids=runids[0] if runids and runids[0] else None,
        targets=[],
        tasks=db_param_convert(tasks),
        algs=db_param_convert(algs),
        svs=db_param_convert(svs),
        vals=None,
    )
    return build_return_object(engine.facet(parameters))
