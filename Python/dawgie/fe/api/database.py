'''The methods for /api/database'''

from dawgie.fe.basis import build_return_object

import dawgie.db
import dawgie.pl.schedule


def runid_max():
    return build_return_object(max([1, dawgie.db.next() - 1]))


def runnables():
    return build_return_object(
        sorted(dawgie.pl.schedule.tasks(), key=str.casefold)
    )


def search(
    runids: str = None,
    targets: str = None,
    tasks: str = None,
    algs: str = None,
    svs: str = None,
    vals: str = None,
):
    return


def targets():
    return build_return_object(
        sorted(dawgie.db.targets(True), key=str.casefold)
    )
