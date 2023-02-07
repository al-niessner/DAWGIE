#! /usr/bin/env python3
'''
COPYRIGHT:
Copyright (c) 2015-2023, California Institute of Technology ("Caltech").
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
import sys

# pylint: disable=protected-access,too-many-arguments
def consume (runid, tn, taskn, algn, svn, vn):
    req = [runid, tn, taskn, algn, svn, vn]
    if all ((x is None for x in req)):
        print ('All parameters are None which means it would be simpler to delete and restart the database. Cowardly doing nothing.')
        logging.getLogger (__name__).warning ('Cowardly doing nothing.')
        return

    dawgie.db.open()
    for k in dawgie.db._prime_keys():
        ids = k.split ('.')
        ids[0] = int (ids[0])

        if all (((e is None or i == e)
                 for i,e in zip (ids, req))): dawgie.db.remove (*ids)
        pass
    dawgie.db.close()
    return

if __name__ == '__main__':
    # main blocks always look the same; pylint: disable=duplicate-code
    root = os.path.dirname (__file__)
    for i in range(4): root = os.path.join (root, '..')
    root = os.path.abspath (root)
    sys.path.append (root)

    import dawgie.context
    import dawgie.db
    import dawgie.db.tools.util
    import dawgie.util

    unique_fn = '.'.join (['worm', getpass.getuser(), 'log'])
    ap = argparse.ArgumentParser(description='Crawls through the database and removes all the matching keys from the primary table. It does not remove the referenced data in the store. There is no undo of this operation and it must be done to a database that is not active (the pipeline is not running.')
    ap.add_argument ('-l', '--log-file', default=unique_fn, required=False,
                     help='a filename to put all of the log messages into [%(default)s]')
    ap.add_argument ('-L', '--log-level', default=logging.INFO, required=False,
                     type=dawgie.util.log_level,
                     help='set the verbosity that you want where a smaller number means more verbose [logging.INFO]')
    dawgie.db.tools.util.add_arguments (ap)
    dawgie.context.add_arguments (ap)
    args = ap.parse_args()
    dawgie.context.override (args)
    logging.basicConfig (filename=os.path.join (dawgie.context.data_log,
                                                args.log_file),
                         level=args.log_level)
    consume (args.run_id, args.target_name, args.task_name,
             args.alg_name, args.state_vector_name, args.value_name)
    pass
else:
    import dawgie.context
    import dawgie.db
    import dawgie.db.tools.util
    import dawgie.util
    pass
