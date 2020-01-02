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

# pylint: disable=import-self,protected-access

import argparse
import datetime
import importlib
import logging
import matplotlib; matplotlib.use ('Agg')
import os
import signal
import sys

class Context(object):
    def __init__(self, address:(str,int), revision:str):
        self.__address = address
        self.__revision = revision
        pass

    def _communicate (self, msg):
        s = dawgie.security.connect (self.__address)
        dawgie.pl.message.send (msg, s)
        m = dawgie.pl.message.receive (s)
        s.close()
        return m

    def abort (self)->bool:
        m = self._communicate (dawgie.pl.message.make
                               (typ=dawgie.pl.message.Type.status,
                                rev=self.__revision))
        return m.type == dawgie.pl.message.Type.response and not m.success

    # pylint: disable=too-many-arguments
    def run (self, factory, ps_hint, jobid, runid, target, timing)->[str]:
        task = (factory (dawgie.util.task_name (factory),
                         ps_hint,
                         runid,
                         target) if runid and target else
                (factory (dawgie.util.task_name (factory),
                          ps_hint,
                          runid) if runid else
                 factory (dawgie.util.task_name (factory),
                          ps_hint,
                          target)))
        setattr (task, 'abort', self.abort)
        dawgie.pl.version.record (task, only=jobid.split('.')[1])
        timing['started'] = datetime.datetime.utcnow()
        task.do (goto=jobid.split('.')[1])
        timing.update (task.timing())
        return task.new_values()
    pass

def _die (signum):
    if signum == signal.SIGABRT:
        raise dawgie.AbortAEError('OS signaled an abort')
    return

def execute (address:(str,int), inc:int, ps_hint:int, rev:str):
    signal.signal (signal.SIGABRT, _die)
    s = dawgie.security.connect (address)
    m = dawgie.pl.message.make (typ=dawgie.pl.message.Type.register,
                                inc=inc,
                                rev=rev)
    dawgie.pl.message.send (m, s)
    m = dawgie.pl.message.make (typ=dawgie.pl.message.Type.wait)
    while m.type == dawgie.pl.message.Type.wait:
        m = dawgie.pl.message.receive (s)
        pass
    s.close()
    ctxt = Context(address, rev)

    if m.type == dawgie.pl.message.Type.task:
        # pylint: disable=bare-except
        if m.ps_hint is not None: ps_hint = m.ps_hint

        dawgie.context.loads (m.context)
        dawgie.context.db_host = address[0]
        dawgie.db.reopen()
        handler = dawgie.pl.logger.TwistedHandler\
                  (host=address[0], port=dawgie.context.log_port)
        logging.basicConfig (handlers=[handler],
                             level=dawgie.context.log_level)
        logging.captureWarnings (True)
        try:
            factory = getattr (importlib.import_module (m.factory[0]),
                               m.factory[1])
            nv = ctxt.run (factory, ps_hint,
                           m.jobid, m.runid, m.target, m.timing)
            m = dawgie.pl.message.make (typ=dawgie.pl.message.Type.response,
                                        inc=m.target,
                                        jid=m.jobid,
                                        rid=m.runid,
                                        suc=True,
                                        tim=m.timing,
                                        val=nv)
        except:
            logging.getLogger(__name__).exception ('Job "%s" failed to execute successfully for run id %s and target "%s"', str (m.jobid), str (m.runid), str (m.target))
            m = dawgie.pl.message.make (typ=dawgie.pl.message.Type.response,
                                        inc=m.target,
                                        jid=m.jobid,
                                        rid=m.runid,
                                        suc=False,
                                        tim=m.timing)
        finally:
            dawgie.db.close()
            s = dawgie.security.connect (address)
            if not ctxt.abort (): dawgie.pl.message.send (m, s)
            pass
    elif m.type == dawgie.pl.message.Type.response and not m.success:
        raise ValueError('Not the same software revisions!')
    else: raise ValueError('Wrong message type: ' + str (m.type))
    return

if __name__ == '__main__':
    import dawgie.context
    import dawgie.pl.aws
    import dawgie.pl.worker
    import dawgie.security

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
           dawgie.pl.aws.execute ((args.hostname, args.port),
                                  args.incarnation,
                                  args.pool_size,
                                  dawgie.context._rev())
        if args.cloud_provider == 'cluster': \
           dawgie.pl.worker.execute ((args.hostname, args.port),
                                     args.incarnation,
                                     args.pool_size,
                                     dawgie.context._rev())
    finally: dawgie.security.finalize()
else:
    import dawgie
    import dawgie.context
    import dawgie.db
    import dawgie.pl.logger
    import dawgie.pl.message
    import dawgie.pl.version
    import dawgie.security
    import dawgie.util
    pass
