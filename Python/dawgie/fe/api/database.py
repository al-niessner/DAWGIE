'''The methods for /api/database'''

import dawgie.db
import dawgie.pl.schedule

from dawgie.db.basis import Params
from dawgie.fe.basis import build_return_object


def runid_max():
    return build_return_object(max([1, dawgie.db.next() - 1]))


def runnables():
    return build_return_object(
        sorted(dawgie.pl.schedule.tasks(), key=str.casefold)
    )


def search(
    runids: str = None,
    targets: [str] = None,
    tasks: [str] = None,
    algs: [str] = None,
    svs: [str] = None,
):
    '''given the facets, find all corresponding state vectors'''
    # pylint: disable=duplicate-code
    parameters = Params(
        runids=runids,
        targets=targets,
        tasks=tasks,
        algs=algs,
        svs=svs,
        vals=None,
    )
    results = dawgie.db.search().find(parameters)
    return build_return_object(results._asdict())


def list_targets():
    return build_return_object(
        sorted(dawgie.db.targets(True), key=str.casefold)
    )
