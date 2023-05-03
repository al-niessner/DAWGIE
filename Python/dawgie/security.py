#! /usr/bin/env python3
'''A utility module to handle socket connection with security.

The security model is ad-hoc and open. It is built upon PGP and is not meant to
hide the security process but rather to make the connection process robust
enough to prevent the casual attempts to probe the ports open for dawgie
processing.

--
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
import datetime
import getpass
import gnupg
import inspect
import logging; log = logging.getLogger (__name__)
import os
import random
import shutil
import socket
import struct
import tempfile
import traceback

_pgp = None
gpgargname = 'gnupghome' if 'gnupghome' in inspect.signature (gnupg.GPG).parameters else 'homedir'

class TwistedWrapper:
    # pylint: disable=too-few-public-methods
    def __init__ (self, protocol, address):
        self.__address = address
        self.__buf = b''
        self.__dr = None
        self.__len = 4
        self.__msg = ''
        self.__phase = self._p1
        self.__p = protocol

        if 0 < dir (protocol).count ('dataReceived'):
            self.__dr = getattr (protocol, 'dataReceived')
            setattr (protocol, 'dataReceived', self.process)
            pass
        return

    def _len (self): return self.__len
    def _phase (self): return self.__phase

    def _p1 (self, data:bytes)->bool:
        log.debug ('pi: %s', str(self.__address))
        result = struct.unpack ('>I', data)[0] == 4
        self.__phase = self._p2
        return result

    def _p2 (self, data:bytes)->bool:
        log.debug ('p2: %s', str(self.__address))
        self.__len = struct.unpack ('>I', data)[0]
        self.__phase = self._p3
        return True

    def _p3 (self, hid:bytes)->bool:
        log.debug ('p3: %s', str(self.__address))
        response = _pgp.verify (hid)

        if response.valid:
            hid = _pgp.decrypt (hid).data.decode()
            log.debug ('Received handshake identification:\n%s', hid)
            self.__msg = 'timestamp: ' + str (datetime.datetime.utcnow())
            self.__msg += '\nunique id: ' + str (random.random())
            msg = struct.pack ('>I', len (self.__msg)) + self.__msg.encode()

            if isinstance (self.__p, socket.socket): self.__p.sendall (msg)
            else: self.__p.transport.write (msg)

            self.__len = 8
            self.__phase = self._p4
            pass
        return response.valid

    def _p4 (self, data:bytes)->bool:
        log.debug ('p4: %s', str(self.__address))
        l = struct.unpack ('>II', data)
        self.__len = l[1]
        self.__phase = self._p5
        return l[0] == 4

    def _p5 (self, reply:bytes)->bool:
        log.debug ('p5: %s', str(self.__address))
        response = _pgp.verify (reply)

        if response.valid:
            reply = _pgp.decrypt (reply).data.decode()
            response.valid = reply.strip() == self.__msg.strip()

            if not response.valid:
                log.warning ('Did not echo my message. Expectation: "%s" but received this "%s".',
                             self.__msg.strip(),
                             reply.strip())
                pass
            pass
        if response.valid and self.__dr is not None:
            setattr (self.__p, 'dataReceived', self.__dr)
            self.__dr (self.__buf)
            self.__buf = b''
            pass
        if response.valid: log.debug ('handshake was successful')

        self.__phase = self._p6
        return response.valid

    @staticmethod
    def _p6 (_ignore:bytes)->bool: return False

    def process (self, data:bytes)->None:
        self.__buf += data

        while self.__len <= len (self.__buf):
            data = self.__buf[:self.__len]
            self.__buf = self.__buf[self.__len:]

            if not self.__phase(data):
                log.error ('failed to pass handshake at %s of %s. Killing the connection to %s.',
                           self.__phase.__name__,
                           str (type (self.__p)),
                           str (self.__address))
                self.__p.transport.loseConnection()
                self.__len = len (self.__buf) + 1  # break out of the while loop
                pass
            pass
        return
    pass

def _my_ip()->str:
    # pylint: disable=bare-except
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 0))  # connecting to a UDP address doesn't send packets
        response = s.getsockname()[0]
    except:
        print ('failed to get host name falling back to localhost')
        traceback.print_exc()
        response = 'localhost'
        pass
    return response

def _recv (s:socket.socket)->str:
    l = struct.unpack ('>I', s.recv(4))[0]
    return s.recv (l)

def _send (s:socket.socket, message:str):
    signed = _pgp.sign (message, passphrase='1234567890', clearsign=True)

    if signed.data: s.sendall (struct.pack ('>I', 4) +
                               struct.pack ('>I', len (signed.data)) +
                               signed.data)
    else:
        log.error (signed.status)
        s.shutdown (socket.SHUT_RDWR)
        s.close()
        pass
    return

def connect (address:(str, int))->socket.socket:
    '''connect using PGP handshaking'''
    s = socket.socket()
    s.connect (address)
    message = ' machine: ' + _my_ip() + '\n'
    message += 'temporal: ' + str (datetime.datetime.utcnow()) + '\n'
    message += 'username: ' + getpass.getuser() + '\n'
    _send (s, message)
    _send (s, _recv (s))
    return s

def delete (keys:[str])->None: _pgp.delete_keys ('\n'.join (keys))
def extend (keys:[str])->None: return _pgp.import_keys ('\n'.join (keys))

def finalize()->None:
    '''clean up after ones self

    Should be called when all done with the security module.
    '''
    shutil.rmtree(getattr(_pgp, gpgargname), ignore_errors=True)
    return

def initialize (path:str=None)->None:
    '''initialize this library with the PGP keyring location

    An empty or None path indicates that we should ignore PGP key verification.
    Rather than have the user maintain a set of keyrings, just have gnuPG use
    a temp directory for the keyring, then import the public an secret keys
    from a directory like `.ssh`.

    File pattern for locating the keys is ...

    path  : path to find the PGP keys dawgie.*.{pub,sec}

    '''
    # pylint: disable=import-outside-toplevel,import-self,protected-access
    import dawgie.security
    dawgie.security._pgp = gnupg.GPG(**{gpgargname:tempfile.mkdtemp()})

    if path and os.path.exists (path) and os.path.isdir (path):
        keys = []
        for fn in filter (lambda fn:fn.startswith ('dawgie.') and
                          (fn.endswith ('.pub') or fn.endswith ('.sec')),
                          os.listdir (path)):
            with open (os.path.join (path,fn), 'rt', encoding="utf-8") as f: \
                 keys.append(f.read())
            pass

        if keys: keys = _pgp.import_keys ('\n'.join (keys))
        else: raise ValueError('No PGP keys found for secure handshake in ' +
                               str(path))
        pass
    return

def pgp(): return _pgp

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='When run as a standalone tool, it used to generate keys for DAWGIE users. The public key generated here should be placed in the DAWGIE OPS gpg home directory and the secret key should go the DAWGIE user gpg home directory. In both cases, they should be -rw------- in that directory. If the DAWGIE loses control of private key, the public should be removed from the DAWGIE gpg home directory. The removal of the public key is equivalent to revoking the key.')
    ap.add_argument ('-e', '--user-email', required=True,
                     help='real email to contact the user')
    ap.add_argument ('-O', '--output-dir', required=True,
                     help='deposit the new keys in the given directory')
    ap.add_argument ('-u', '--user-name', required=True,
                     help='real name in the form "First Last"')
    args = ap.parse_args()
    homedir = tempfile.mkdtemp()
    pgp = gnupg.GPG(**{gpgargname:homedir})
    k = pgp.gen_key (pgp.gen_key_input (key_type='DSA',
                                        name_email=args.user_email,
                                        name_real=args.user_name))
    bn = os.path.join (args.output_dir, 'dawgie.%s.%s')
    with open (bn % (args.user_name, 'pub'), 'tw', encoding="utf-8") as gf: \
         gf.write (pgp.export_keys (k))
    with open (bn % (args.user_name, 'sec'), 'tw', encoding="utf-8") as gf: \
         gf.write (pgp.export_keys (k, True))
    os.chmod (bn % (args.user_name, 'pub'), 0o600)
    os.chmod (bn % (args.user_name, 'sec'), 0o600)
    shutil.rmtree (homedir)
    pass
