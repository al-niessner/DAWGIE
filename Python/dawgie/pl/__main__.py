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

# main modules usually have very similar lines to other mains or inits so
# pylint: disable=duplicate-code

import argparse
import dawgie.context
import dawgie.pl.state
import dawgie.util
import logging
import matplotlib; matplotlib.use("Agg")  # fmt: skip # noqa: E702 # pylint: disable=multiple-statements
import twisted.internet
import sys

from . import _merge
from . import LogFailure


class Start(LogFailure):
    def __init__(self, cmdl_args, label, name):
        LogFailure.__init__(self, label, name)
        self.__args = cmdl_args
        self.__deferred = twisted.internet.defer.Deferred()
        self.__deferred.addCallback(self.run).addErrback(self.log)
        return

    @property
    def callback(self):
        return self.__deferred.callback

    @property
    def deferred(self):
        return self.__deferred

    def run(self, *_args, **_kwds):
        dawgie.context.fsm = dawgie.pl.state.FSM()
        dawgie.context.fsm.args = self.__args
        dawgie.context.fsm.starting_trigger()
        return

    pass


ap = argparse.ArgumentParser(
    description='The main routine to run the fully automated pipeline.'
)
ap.add_argument(
    '-l',
    '--log-file',
    default='dawgie.log',
    required=False,
    help='a filename to put all of the log messages into [%(default)s]',
)
ap.add_argument(
    '-L',
    '--log-level',
    default=logging.ERROR,
    required=False,
    type=dawgie.util.log_level,
    help='set the verbosity that you want where a smaller number means more verbose [logging.WARN]',
)
ap.add_argument(
    '-p',
    '--port',
    default=dawgie.context.fe_port,
    required=False,
    type=int,
    help='server port number for the display [%(default)s]',
)
dawgie.context.add_arguments(ap)
args = ap.parse_args()

if args.port != dawgie.context.fe_port:
    gnew = args.port + dawgie.context.PortOffset.frontend.value
    args.context_cfe_port = _merge(
        dawgie.context.fe_port,
        gnew,
        dawgie.context.PortOffset.certFE.value,
        args.context_cfe_port,
    )
    args.context_cloud_port = _merge(
        dawgie.context.fe_port,
        gnew,
        dawgie.context.PortOffset.cloud.value,
        args.context_cloud_port,
    )
    args.context_db_port = _merge(
        dawgie.context.fe_port,
        gnew,
        dawgie.context.PortOffset.shelve.value,
        args.context_db_port,
    )
    args.context_farm_port = _merge(
        dawgie.context.fe_port,
        gnew,
        dawgie.context.PortOffset.farm.value,
        args.context_farm_port,
    )
    args.context_log_port = _merge(
        dawgie.context.fe_port,
        gnew,
        dawgie.context.PortOffset.log.value,
        args.context_log_port,
    )
    dawgie.context.fe_port = (
        args.port + dawgie.context.PortOffset.frontend.value
    )
    pass

dawgie.context.log_level = args.log_level
dawgie.context.override(args)
twisted.internet.reactor.callLater(
    0, Start(args, 'starting the pipeline', 'dawgie.pl').callback, 'main'
)
twisted.internet.reactor.run()
print('calling system exit...')
sys.exit()
