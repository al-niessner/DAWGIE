#!/usr/bin/env python3
'''
COPYRIGHT:
Copyright (c) 2015-2025, California Institute of Technology ("Caltech").
U.S. Government sponsorship acknowledged.

All rights reserved.

LICENSE:
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

- Neither the name of Caltech nor its operating division, the Jet
Propulsion Laboratory, nor the names of its contributors may be used to
endorse or promote products derived from this software without specific prior
written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

NTR:
'''

import argparse
import dawgie.db.shelve.util
import logging; log = logging.getLogger(__name__)  # fmt: skip # noqa: E702 # pylint: disable=multiple-statements
import os
import shelve
import sys

from dawgie.db.shelve.util import LocalVersion


def _cur(conn):
    '''consolidate the pylint disabling'''
    return dawgie.db.post._cur(conn)  # pylint: disable=protected-access


def _latest(all_vers: bool, rows):
    '''reduce the table to latest if desired

    rows must be of the form:

        [0]  = primary key
        [1]  = name
        [2]  = parent
        [-3] = design
        [-2] = implementation
        [-1] = bugfix
    '''
    if all_vers:
        return rows

    latest = {}
    for row in rows:
        key = (row[1], row[2])
        if key in latest:
            ver = LocalVersion(row[-3:])
            if ver.newer(than=LocalVersion(latest[key][-3:]).version):
                latest[key] = row
        else:
            latest[key] = row
        pass
    return latest.values()


def convert_algorithm_db(conn, fn: str, trans: {int: int}, all_vers: bool):
    '''convert the postgres Algorithm table to compatible shelve format'''
    cur = _cur(conn)
    cur.execute('SELECT * from Algorithm;')
    rows = cur.fetchall()
    index = []
    table = shelve.open(fn)
    tdb = {}
    for r in _latest(all_vers, rows):
        name = r[1]
        parent = trans[r[2]]
        version = LocalVersion(r[-3:])
        tdb[r[0]] = len(index)
        dawgie.db.shelve.util.append(name, table, index, parent, version)
        pass
    table.close()
    conn.commit()
    cur.close()
    return tdb


def convert_prime_db(conn, fn, data, all_vers: bool):
    '''convert the postgres Prime table to compatible shelve format'''
    cur = _cur(conn)
    table = {}
    cur.execute(
        'SELECT run_ID,tn_ID,task_ID,alg_ID,sv_ID,val_ID,blob_name '
        + 'FROM Prime WHERE tn_ID = ANY(%s) AND task_ID = ANY(%s) AND '
        + 'alg_ID = ANY(%s) AND sv_ID = ANY(%s) AND val_ID = ANY(%s);',
        (
            list(data['target']),
            list(data['task']),
            list(data['alg']),
            list(data['state']),
            list(data['value']),
        ),
    )
    for rid, tnid, tid, aid, svid, vid, bn in sorted(
        cur.fetchall(), key=lambda t: t[0]
    ):
        k = (
            rid if all_vers else 1,
            data['target'][tnid],
            data['task'][tid],
            data['alg'][aid],
            data['state'][svid],
            data['value'][vid],
        )
        table[str(k)] = bn
        pass
    conn.commit()
    cur.close()
    with shelve.open(fn) as db:
        db.update(table)
    return


def convert_state_vector_db(conn, fn: str, trans: {int: int}, all_vers: bool):
    '''convert the postgres StateVector table to compatible shelve format'''
    cur = _cur(conn)
    cur.execute(
        "SELECT * from StateVector where alg_ID = ANY(%s);", (list(trans),)
    )
    rows = cur.fetchall()
    index = []
    table = shelve.open(fn)
    tdb = {}
    for r in _latest(all_vers, rows):
        name = r[1]
        parent = trans[r[2]]
        version = LocalVersion(r[-3:])
        tdb[r[0]] = len(index)
        dawgie.db.shelve.util.append(name, table, index, parent, version)
        pass
    table.close()
    conn.commit()
    cur.close()
    return tdb


def convert_target_db(conn, fn):
    '''convert the postgres Target table to compatible shelve format'''
    cur = _cur(conn)
    cur.execute('SELECT * from Target;')
    rows = cur.fetchall()
    index = []
    table = shelve.open(fn)
    tdb = {}
    for r in rows:
        tdb[r[0]] = len(index)
        dawgie.db.shelve.util.append(r[1], table, index)
        pass
    table.close()
    conn.commit()
    cur.close()
    return tdb


def convert_task_db(conn, fn):
    '''convert the postgres Task table to compatible shelve format'''
    cur = _cur(conn)
    cur.execute('SELECT * from Task;')
    rows = cur.fetchall()
    index = []
    table = shelve.open(fn)
    tdb = {}
    for r in rows:
        tdb[r[0]] = len(index)
        dawgie.db.shelve.util.append(r[1], table, index)
        pass
    table.close()
    conn.commit()
    cur.close()
    return tdb


def convert_value_vector_db(conn, fn, trans: {int: int}, all_vers: bool):
    '''conver the postgres Value table to compatile shelve format'''
    cur = _cur(conn)
    cur.execute("SELECT * from Value where sv_ID = ANY(%s);", (list(trans),))
    rows = cur.fetchall()
    index = []
    table = shelve.open(fn)
    tdb = {}
    for r in _latest(all_vers, rows):
        name = r[1]
        parent = trans[r[2]]
        version = LocalVersion(r[-3:])
        tdb[r[0]] = len(index)
        dawgie.db.shelve.util.append(name, table, index, parent, version)
        pass
    table.close()
    conn.commit()
    cur.close()
    return tdb


def main(all_vers, dpath):
    '''sequential steps to move postgres DB to shelve'''
    conn = dawgie.db.post._conn()  # pylint: disable=protected-access
    basefn = f'{dpath}/{dawgie.context.db_post2shelve_prefix}'
    os.system(f"mkdir -p {dpath}")
    for suffix in ['alg', 'prime', 'state', 'target', 'task', 'value']:
        fn = f'{basefn}.{suffix}'
        if os.path.isfile(fn):
            os.unlink(fn)
        pass

    log.info('-------------target-----------')
    target_k = convert_target_db(conn, f'{basefn}.target')
    log.info('-------------task-----------')
    task_k = convert_task_db(conn, f'{basefn}.task')
    log.info('-------------alg-----------')
    alg_k = convert_algorithm_db(conn, f'{basefn}.alg', task_k, all_vers)
    log.info('-------------state-----------')
    state_k = convert_state_vector_db(conn, f'{basefn}.state', alg_k, all_vers)
    log.info('-------------value-----------')
    value_k = convert_value_vector_db(
        conn, f'{basefn}.value', state_k, all_vers
    )
    log.info('-------------prime-----------')
    pk_translation = {
        'target': target_k,
        'task': task_k,
        'alg': alg_k,
        'state': state_k,
        'value': value_k,
    }
    log.info('-------------convert-----------')
    convert_prime_db(conn, f'{basefn}.prime', pk_translation, all_vers)
    conn.close()
    pass


if __name__ == "__main__":
    # main blocks always look the same; pylint: disable=duplicate-code
    root = os.path.dirname(__file__)
    for i in range(4):
        root = os.path.join(root, '..')
    root = os.path.abspath(root)
    sys.path.append(root)

    import dawgie.context
    import dawgie.db
    import dawgie.db.tools.util
    import dawgie.util
    import dawgie.db.post

    ap = argparse.ArgumentParser(
        description='Translates postgresql database to shelve database. This is a one-way translation, no way to go back.'
    )
    ap.add_argument(
        '-a',
        '--all',
        action='store_true',
        default=False,
        help='translate all versions instead of just latest',
    )
    ap.add_argument(
        '-l',
        '--log-file',
        default=None,
        required=False,
        help='a filename to put all of the log messages into [stdout]',
    )
    ap.add_argument(
        '-L',
        '--log-level',
        default=logging.WARNING,
        required=False,
        type=dawgie.util.log_level,
        help='set the verbosity that you want where a smaller number means more verbose [logging.WARNING]',
    )
    ap.add_argument(
        '-O',
        '--output-path',
        required=True,
        type=str,
        help='a path to place your converted shelve files into',
    )
    ap.add_argument(
        '-p',
        '--prefix',
        default=dawgie.context.db_post2shelve_prefix,
        required=False,
        help='a filename prefix to put all the post2shelve db files into [%(default)s]',
    )
    dawgie.context.add_arguments(ap)
    args = ap.parse_args()
    dawgie.context.override(args)
    dawgie.context.db_post2shelve_prefix = args.prefix
    main(args.all, args.output_path)
else:
    import dawgie.context
    import dawgie.db.post

    pass
