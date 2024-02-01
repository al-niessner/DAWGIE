'''

COPYRIGHT:
Copyright (c) 2015-2024, California Institute of Technology ("Caltech").
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

import base64
import dawgie.context
import dawgie.pl.state
dawgie.context.fsm = dawgie.pl.state.FSM()
import dawgie.pl.message
import dawgie.pl.worker.aws
import dawgie.security
import gnupg
import multiprocessing
import os
import shutil
import tempfile
import time
import unittest

class AWS(unittest.TestCase):
    failed = False
    def test_handshake (self):
        global _https_in,_https_out,_sqs_in,_sqs_out
        kdir = tempfile.mkdtemp()
        _pgp = gnupg.GPG(gnupghome=kdir)
        ab = _pgp.gen_key(_pgp.gen_key_input(key_type='DSA',
                                             subkey_type='DSA',
                                             passphrase='1234567890',
                                             name_email='aws-bot@cloud.com',
                                             name_real='aws-bot'))
        db = _pgp.gen_key(_pgp.gen_key_input(key_type='DSA',
                                             subkey_type='DSA',
                                             passphrase='1234567890',
                                             name_email='dawgie-bot@cloud.com',
                                             name_real='dawgie-bot'))
        with open (os.path.join (kdir, 'dawgie.aws.pub'), 'tw') as f: \
             f.write (_pgp.export_keys ([ab.fingerprint],
                                        passphrase='1234567890'))
        with open (os.path.join (kdir, 'dawgie.aws.sec'), 'tw') as f: \
             f.write (_pgp.export_keys ([ab.fingerprint], secret=True,
                                        passphrase='1234567890'))
        with open (os.path.join (kdir, 'dawgie.bot.pub'), 'tw') as f: \
             f.write (_pgp.export_keys ([db.fingerprint],
                                        passphrase='1234567890'))
        with open (os.path.join (kdir, 'dawgie.bot.sec'), 'tw') as f: \
             f.write (_pgp.export_keys ([db.fingerprint], secret=True,
                                        passphrase='1234567890'))
        dawgie.security.initialize (kdir)
        _https_in, _https_out = multiprocessing.Queue(),multiprocessing.Queue()
        originals = (dawgie.pl.worker.aws._advertise,
                     dawgie.pl.worker.aws._interview,
                     dawgie.pl.worker.aws._hire,
                     dawgie.pl.worker.aws._https_push,
                     dawgie.pl.worker.aws._sqs_pop,
                     dawgie.pl.worker.aws._sqs_push)
        _sqs_in,_sqs_out = multiprocessing.Queue(),multiprocessing.Queue()
        task = multiprocessing.Process(target=_aws, args=(_https_out, _https_in,
                                                          _sqs_out, _sqs_in,
                                                          kdir))
        task.start()
        _subs()
        do = dawgie.pl.worker.aws.Connect(dawgie.pl.message.make(val=kdir), _respond, _callLater)
        do.advertise()
        self.assertFalse (AWS.failed)
        task.join()
        msg = _sqs_in.get()
        _subs (originals)
        try: shutil.rmtree (kdir)
        except FileNotFoundError: print ('failed to clean up')
        self.assertTrue ('id' in msg)
        self.assertTrue ('payload' in msg)
        self.assertTrue ('pubkey' in msg)
        self.assertTrue ('seckey' in msg)
        m = dawgie.pl.message.loads (base64.b64decode (msg['payload']))
        self.assertEqual (kdir, m.values)
        return
    pass

def _aws (https_in, https_out, sqs_in, sqs_out, kdir):
    global _https_in,_https_out,_sqs_in,_sqs_out
    _https_in = https_in
    _https_out = https_out
    _sqs_in = sqs_in
    _sqs_out = sqs_out
    _subs()
    dawgie.security.initialize (kdir)
    _https_out.put (dawgie.pl.worker.aws.exchange (_https_in.get()))
    _https_out.put (dawgie.pl.worker.aws.exchange (_https_in.get()))
    _https_out.put (dawgie.pl.worker.aws.exchange (_https_in.get()))
    return

def _advertise(): return 'position posted'
def _interview(): return 1,'Healthy','InService','i-4',True
def _hire(iid): return

def _callLater (offset, cb, *args):
    if 0 < offset: time.sleep (offset)
    cb (*args)
    return

def _https_push (msg):
    _https_out.put (msg)
    return _https_in.get()

def _respond (*args): AWS.failed = True

def _sqs_pop():
    return _sqs_in.get()

def _sqs_push (msg):
    return _sqs_out.put (msg)

def _subs (funcs=(_advertise,_interview,_hire,_https_push,_sqs_pop,_sqs_push)):
    dawgie.pl.worker.aws._advertise = funcs[0]
    dawgie.pl.worker.aws._interview = funcs[1]
    dawgie.pl.worker.aws._hire = funcs[2]
    dawgie.pl.worker.aws._https_push = funcs[3]
    dawgie.pl.worker.aws._sqs_pop = funcs[4]
    dawgie.pl.worker.aws._sqs_push = funcs[5]
    return

if __name__ == '__main__': AWS().test_handshake()
