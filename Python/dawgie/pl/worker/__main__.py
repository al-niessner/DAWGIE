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

# pylint: disable=import-self,protected-access

import argparse
import dawgie.context
import dawgie.pl.state
dawgie.context.fsm = dawgie.pl.state.FSM()  # needs to be here for aws import
import dawgie.pl.worker
import dawgie.pl.worker.aws
import dawgie.pl.worker.cluster
import dawgie.security
import matplotlib; matplotlib.use ('Agg')
import os
import sys

ap = argparse.ArgumentParser(description='The main routine to run and individual worker.')
ap.add_argument ('-a', '--ae-path', required=True, type=str,
                 help='the path to the AE')
ap.add_argument ('-b', '--ae-base-package', required=True, type=str,
                 help='the AE base package like exo.spec.ae')
ap.add_argument ('-c', '--cloud-provider', choices=['aws', 'cluster'],
                 default='cluster', required=False,
                 help='running on which cloud provider [%(default)s]')
ap.add_argument ('-g', '--gpg-home', default='~/.gnupg', required=False,
                 help='location to find the PGP keys [%(default)s]')
ap.add_argument ('-i', '--incarnation', required=True, type=int,
                 help='Number of times this worker has been asked to start')
ap.add_argument ('-n', '--hostname', required=True, type=str,
                 help='farm server hostname')
ap.add_argument ('-p', '--port', required=True, type=int,
                 help='farm server port')
ap.add_argument ('-s', '--pool-size', default=4, required=False, type=int,
                 help='suggested pool size for those that want to use multiprocessing')
args = ap.parse_args()
dawgie.context.ae_base_path = args.ae_path
dawgie.context.ae_base_package = args.ae_base_package
python_path = dawgie.context.ae_base_path
for junk in dawgie.context.ae_base_package.split ('.'):\
    python_path = os.path.dirname (python_path)
sys.path.insert (0, python_path)
dawgie.security.initialize (os.path.expandvars
                            (os.path.expanduser
                             (args.gpg_home)))
try:
    if args.cloud_provider == 'aws': \
       dawgie.pl.worker.aws.execute ((args.hostname, args.port),
                                     args.incarnation,
                                     args.pool_size,
                                     dawgie.context._rev())
    if args.cloud_provider == 'cluster': \
       dawgie.pl.worker.cluster.execute ((args.hostname, args.port),
                                         args.incarnation,
                                         args.pool_size,
                                         dawgie.context._rev())
finally: dawgie.security.finalize()
