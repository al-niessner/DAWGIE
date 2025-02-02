#! /usr/bin/env python3
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
import getpass
import logging
import os
import pickle
import sys


class FakeItem(dict):
    def __init__(self, name, runid, svl):
        dict.__init__(self)
        self.__name = name
        self.__runid = runid
        self.__svl = svl
        return

    def _name(self):
        return self.__name

    def _runid(self):
        return self.__runid

    def abort(self):
        return False

    def name(self):
        return self.__name

    def state_vectors(self):
        return self.__svl

    pass


# pylint: disable=protected-access,too-many-arguments,too-many-positional-arguments,used-before-assignment
def info(ofn, runid, tn, taskn, algn, svn):
    if any(
        [runid is None, tn is None, taskn is None, algn is None, svn is None]
    ):
        logging.getLogger(__name__).critical(
            'All inputs are required and must be valid'
        )
        print('All inputs are required and must be valid')
        pass
    else:
        if ofn is None:
            ofn = '.'.join([tn, taskn, algn, svn, 'pkl'])

        dawgie.db.reopen()
        ds = dawgie.db.connect(
            FakeItem(algn, runid, [FakeItem(svn, runid, [])]),
            FakeItem(taskn, runid, []),
            tn,
        )
        ds.load()
        with open(ofn, 'wb') as file:
            pickle.dump(
                dict(ds._alg().state_vectors()[0]),
                file,
                pickle.HIGHEST_PROTOCOL,
            )
        dawgie.db.close()
        dawgie.security.finalize()
        pass
    return


if __name__ == '__main__':
    # main blocks always look the same; pylint: disable=duplicate-code
    root = os.path.dirname(__file__)
    for i in range(4):
        root = os.path.join(root, '..')
    root = os.path.abspath(root)
    sys.path.append(root)

    import dawgie.context
    import dawgie.db
    import dawgie.util

    UNIQUE_FN = '.'.join(['extract', getpass.getuser(), 'log'])
    ap = argparse.ArgumentParser(
        description='Extract a single state vector from a database.'
    )
    ap.add_argument(
        '-l',
        '--log-file',
        default=UNIQUE_FN,
        required=False,
        help='a filename to put all of the log messages into [%(default)s]',
    )
    ap.add_argument(
        '-L',
        '--log-level',
        default=logging.INFO,
        required=False,
        type=dawgie.util.log_level,
        help='set the verbosity that you want where a smaller number means more verbose [logging.INFO]',
    )
    ap.add_argument(
        '-o',
        '--output-filename',
        default=None,
        type=str,
        help='output filename and if none is given then a name will be generated: <target name>.<task name>.<algorithm name>.<state vector name>.pkl',
    )
    ap.add_argument(
        '-r',
        '--run-id',
        default=-1,
        required=False,
        type=int,
        help='The run ID to match where -1 means latest [%(default)s]',
    )
    ap.add_argument(
        '-T',
        '--target-name',
        required=True,
        type=str,
        help='The target name to match',
    )
    ap.add_argument(
        '-t',
        '--task-name',
        required=True,
        type=str,
        help='The task name to match',
    )
    ap.add_argument(
        '-a',
        '--alg-name',
        required=True,
        type=str,
        help='The algorithm name to match',
    )
    ap.add_argument(
        '-s',
        '--state-vector-name',
        required=True,
        type=str,
        help='The state vector name to match',
    )
    dawgie.context.add_arguments(ap)
    args = ap.parse_args()
    dawgie.context.override(args)
    logging.basicConfig(
        filename=os.path.join(dawgie.context.data_log, args.log_file),
        level=args.log_level,
    )
    dawgie.security.initialize(
        path=os.path.expandvars(
            os.path.expanduser(dawgie.context.guest_public_keys)
        ),
        myname=dawgie.context.ssl_pem_myname,
        myself=os.path.expandvars(
            os.path.expanduser(dawgie.context.ssl_pem_myself)
        ),
        system=dawgie.context.ssl_pem_file,
    )

    info(
        args.output_filename,
        args.run_id,
        args.target_name,
        args.task_name,
        args.alg_name,
        args.state_vector_name,
    )
    pass
else:
    import dawgie.context
    import dawgie.db
    import dawgie.util

    pass
