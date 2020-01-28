#! /usr/bin/env python3
'''
COPYRIGHT:
Copyright (c) 2015-2020, California Institute of Technology ("Caltech").
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
import logging
import matplotlib; matplotlib.use("Agg")
import os
import sys
import twisted.internet

def _main():
    dawgie.pl.start.fsm = dawgie.pl.state.FSM()
    dawgie.pl.start.fsm.args = dawgie.pl.start.args
    dawgie.pl.start.fsm.starting_trigger()
    return

def _merge (old:int, new:int, offset:int, req:int):
    return req if (old + offset) != req else (new + offset)

if __name__ == '__main__':
    root = os.path.dirname (__file__)
    for i in range(3): root = os.path.join (root, '..')
    root = os.path.abspath (root)
    sys.path.insert (0,root)

    import dawgie.context
    import dawgie.pl.start  # pylint: disable=import-self
    import dawgie.tools.submit
    import dawgie.util

    ap = argparse.ArgumentParser(description='The main routine to run the fully automated pipeline.')
    ap.add_argument ('-l', '--log-file', default='dawgie.log', required=False,
                     help='a filename to put all of the log messages into [%(default)s]')
    ap.add_argument ('-L', '--log-level', default=logging.ERROR, required=False,
                     type=dawgie.util.log_level,
                     help='set the verbosity that you want where a smaller number means more verbose [logging.ERROR]')
    ap.add_argument ('-p', '--port', default=dawgie.context.fe_port,
                     required=False, type=int,
                     help='server port number for the display [%(default)s]')
    ap.add_argument('-r', '--repo-dir', default=dawgie.tools.submit.repo_dir, required=False,
                    help='set the pre_ops repo directory where you want to do the merging [%(default)s]')
    dawgie.context.add_arguments (ap)
    dawgie.pl.start.args = ap.parse_args()

    if dawgie.pl.start.args.port != dawgie.context.fe_port:
        # pylint: disable=protected-access
        gnew = dawgie.pl.start.args.port +\
               dawgie.context.PortOffset.frontend.value
        dawgie.pl.start.args.context_cloud_port = \
                               _merge (dawgie.context.fe_port,
                                       gnew,
                                       dawgie.context.PortOffset.cloud.value,
                                       dawgie.pl.start.args.context_cloud_port)
        dawgie.pl.start.args.context_db_port = \
                               _merge (dawgie.context.fe_port,
                                       gnew,
                                       dawgie.context.PortOffset.shelf.value,
                                       dawgie.pl.start.args.context_db_port)
        dawgie.pl.start.args.context_farm_port = \
                               _merge (dawgie.context.fe_port,
                                       gnew,
                                       dawgie.context.PortOffset.farm.value,
                                       dawgie.pl.start.args.context_farm_port)
        dawgie.pl.start.args.context_log_port = \
                               _merge (dawgie.context.fe_port,
                                       gnew,
                                       dawgie.context.PortOffset.log.value,
                                       dawgie.pl.start.args.context_log_port)
        dawgie.context.fe_port = dawgie.pl.start.args.port + \
                                   dawgie.context.PortOffset.frontend.value
        pass

    dawgie.context.log_level = dawgie.pl.start.args.log_level
    dawgie.context.override (dawgie.pl.start.args)
    twisted.internet.reactor.callLater (0, dawgie.pl.LogDeferredException(dawgie.pl.start._main, 'starting the pipeline', __name__).callback, None)  # pylint:  disable=protected-access
    twisted.internet.reactor.run()
    print ('calling system exit...')
    sys.exit()
else:
    import dawgie.context
    import dawgie.pl.start  # pylint: disable=import-self
    import dawgie.pl.state
    import dawgie.tools.submit
    import dawgie.util

    fsm = dawgie.pl.state.FSM()
    pass
