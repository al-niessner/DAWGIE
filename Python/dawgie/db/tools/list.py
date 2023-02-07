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

def info (runid, tn, taskn, algn, svn):
    # pylint: disable=protected-access
    dawgie.db.reopen()
    svl = list ({'.'.join (k.split ('.')[:-1]) for k in dawgie.db._prime_keys()})
    dawgie.db.close()
    dawgie.security.finalize()
    svl.sort()
    for sv in svl:
        grunid,gtn,gtaskn,galgn,gsvn = sv.split ('.')
        if all ([runid is None or runid == int(grunid),
                 tn is None or tn == gtn,
                 taskn is None or taskn == gtaskn,
                 algn is None or algn == galgn,
                 svn is None or svn == gsvn]): print (sv)
        pass
    return

if __name__ == '__main__':
    # main blocks always look the same; pylint: disable=duplicate-code
    root = os.path.dirname (__file__)
    for i in range(4): root = os.path.join (root, '..')
    root = os.path.abspath (root)
    sys.path.append (root)

    import dawgie.context
    import dawgie.db
    import dawgie.util

    unique_fn = '.'.join (['list', getpass.getuser(), 'log'])
    ap = argparse.ArgumentParser(description='List all available state vectors. Wihtout specifying anything, all state vectors are listed. The user can then further limit the list by adding bits and pieces.')
    ap.add_argument ('-l', '--log-file', default=unique_fn, required=False,
                     help='a filename to put all of the log messages into [%(default)s]')
    ap.add_argument ('-L', '--log-level', default=logging.INFO, required=False,
                     type=dawgie.util.log_level,
                     help='set the verbosity that you want where a smaller number means more verbose [logging.INFO]')
    ap.add_argument ('-r', '--run-id', default=None, required=False, type=int,
                     help='The run ID to match where -1 means latest [Any]')
    ap.add_argument ('-T', '--target-name', default=None, required=False, type=str,
                     help='The target name to match [Any]')
    ap.add_argument ('-t', '--task-name', default=None, required=False, type=str,
                     help='The task name to match [Any]')
    ap.add_argument ('-a', '--alg-name', default=None, required=False, type=str,
                     help='The algorithm name to match [Any]')
    ap.add_argument ('-s', '--state-vector-name', default=None, required=False, type=str,
                     help='The state vector name to match [Any]')
    dawgie.context.add_arguments (ap)
    args = ap.parse_args()
    dawgie.context.override (args)
    logging.basicConfig (filename=os.path.join (dawgie.context.data_log,
                                                args.log_file),
                         level=args.log_level)

    dawgie.security.initialize (os.path.expandvars
                                (os.path.expanduser
                                 (dawgie.context.gpg_home)))
    info (args.run_id,
          args.target_name,
          args.task_name,
          args.alg_name,
          args.state_vector_name)
    pass
else:
    import dawgie.context
    import dawgie.db
    import dawgie.util
    pass
