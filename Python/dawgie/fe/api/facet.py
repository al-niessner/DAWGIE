'''the methods to facet/filter given user constrants'''

import dawgie.db

from dawgie.db.basis import Params
from dawgie.fe.basis import build_return_object


def alg(runids: str, targets: [str], tasks: [str], svs: [str]):
    '''facet the algorithm name

    All parameters must be a string or list with content or None. An empty list
    will cause an error in later processing.
    '''
    # pylint: disable=duplicate-code
    engine = dawgie.db.search()
    parameters = Params(
        runids=runids,
        targets=targets,
        tasks=tasks,
        algs=[],
        svns=svs,
        vals=None,
    )
    return build_return_object(engine.facet(parameters))


def sv(runids: str, targets: [str], tasks: [str], algs: [str]):
    '''facet the state vector name

    All parameters must be a string or list with content or None. An empty list
    will cause an error in later processing.
    '''
    # pylint: disable=duplicate-code
    engine = dawgie.db.search()
    parameters = Params(
        runids=runids,
        targets=targets,
        tasks=tasks,
        algs=algs,
        svns=[],
        vals=None,
    )
    return build_return_object(engine.facet(parameters))


def task(runids: str, targets: [str], algs: [str], svs: [str]):
    '''facet the task name

    All parameters must be a string or list with content or None. An empty list
    will cause an error in later processing.
    '''
    # pylint: disable=duplicate-code
    engine = dawgie.db.search()
    parameters = Params(
        runids=runids, targets=targets, tasks=[], algs=algs, svns=svs, vals=None
    )
    return build_return_object(engine.facet(parameters))


def target(runids: str, tasks: [str], algs: [str], svs: [str]):
    '''facet the target name

    All parameters must be a string or list with content or None. An empty list
    will cause an error in later processing.
    '''
    # pylint: disable=duplicate-code
    engine = dawgie.db.search()
    parameters = Params(
        runids=runids, targets=[], tasks=tasks, algs=algs, svns=svs, vals=None
    )
    return build_return_object(engine.facet(parameters))
