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
import dawgie
import dawgie.context
import dawgie.db.util
import dawgie.util
import getpass
import logging
import os
import sys

from dawgie.db.shelve.enums import Method


def make_dir(dst):
    return os.system(f"mkdir -p {dst}")


def dbcopy(host, port, dst, method, gateway):
    print(host, port, dst, method, gateway)
    dawgie.db.reopen()

    make_dir(dst)
    dawgie.db.copy(dst=dst, method=method, gateway=gateway)
    dawgie.db.close()

    return 0


if __name__ == "__main__":
    root = os.path.dirname(__file__)
    for i in range(4):
        root = os.path.join(root, '..')
    root = os.path.abspath(root)
    sys.path.append(root)

    import dawgie.db

    UNIQUE_FN = '.'.join(['copy', getpass.getuser(), 'log'])

    ap = argparse.ArgumentParser(
        description='Safely copies database to a specified location. This tool is necessary when creating a database sandbox.\n\nExample:\n    sandbox.py --context-db-copy-path=/tmp/mysandboxdb --context-db-port=9999'
    )
    # ignore tools that use similar arguments
    # pylint: disable=duplicate-code
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
        '-m',
        '--method',
        default=Method.connector,
        required=False,
        help='method to copy database. Options are connector, rsync, scp, cp. Please use connector as a last resort. [%(default)s]',
    )
    dawgie.context.add_arguments(ap)
    ap.add_argument(
        '-g',
        '--gateway',
        default=dawgie.context.db_host,
        required=False,
        help='Database source machine. [%(default)s]',
    )
    # pylint: enable=duplicate-code

    args = ap.parse_args()
    dawgie.context.override(args)

    logging.basicConfig(
        filename=os.path.join(dawgie.context.data_log, args.log_file),
        level=args.log_level,
    )

    if args.method == "connector":
        args.method = Method.connector
    elif args.method == "rsync":
        args.method = Method.rsync
    elif args.method == "scp":
        args.method = Method.scp
    elif args.method == "cp":
        args.method = Method.cp

    RETURN_CODE = dbcopy(
        args.context_db_host,
        int(args.context_db_port),
        args.context_db_copy_path,
        args.method,
        args.gateway,
    )
    print(RETURN_CODE)
    sys.exit(RETURN_CODE)
