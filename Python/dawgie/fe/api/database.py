'''The methods for /api/database'''

from dawgie.fe.basis import build_return_object

import dawgie.db
import dawgie.pl.schedule


def runnables():
    return build_return_object(
        sorted(dawgie.pl.schedule.tasks(), key=str.casefold)
    )


def search(
    runid: int = None,
    target: str = None,
    task: str = None,
    alg: str = None,
    sv: str = None,
    val: str = None,
):
    return


def targets():
    return build_return_object(
        sorted(dawgie.db.targets(True), key=str.casefold)
    )
