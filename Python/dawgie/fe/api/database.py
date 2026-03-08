'''The methods for /api/database'''

import dawgie.db
import dawgie.pl.schedule
import logging

from .. import svrender

from dawgie.db.basis import Params
from dawgie.fe.basis import build_return_object, db_param_convert

LOG = logging.getLogger(__name__)
VIEW = svrender.Defer()


def runid_max():
    return build_return_object(max([1, dawgie.db.next() - 1]))


def runnables():
    return build_return_object(
        sorted(dawgie.pl.schedule.tasks(), key=str.casefold)
    )


# pylint: disable=too-many-arguments,too-many-positional-arguments
def search(
    runids: [str] = None,
    targets: [str] = None,
    tasks: [str] = None,
    algs: [str] = None,
    svs: [str] = None,
    index: int = 0,
    limit: int = None,
):
    '''given the facets, find all corresponding state vectors'''
    # pylint: disable=duplicate-code
    parameters = Params(
        runids=runids[0] if runids and runids[0] else None,
        targets=db_param_convert(targets),
        tasks=db_param_convert(tasks),
        algs=db_param_convert(algs),
        svs=db_param_convert(svs),
        vals=None,
    )
    index = int(index[0]) if index and index[0] else 0
    limit = int(limit[0]) if limit and limit[0] else None
    results = dawgie.db.search().find(parameters, index, limit)
    return build_return_object(results._asdict())


# pylint: enable=too-many-arguments,too-many-positional-arguments


def list_targets():
    return build_return_object(
        sorted(dawgie.db.targets(True), key=str.casefold)
    )
