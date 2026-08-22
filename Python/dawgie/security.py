#! /usr/bin/env python3
'''A utility module to handle socket connection with security.

The security model is ad-hoc and open. It is built upon PGP and is not meant to
hide the security process but rather to make the connection process robust
enough to prevent the casual attempts to probe the ports open for dawgie
processing.

--
COPYRIGHT:
Copyright (c) 2015-2026, California Institute of Technology ("Caltech").
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
import enum
import getpass
import gnupg
import importlib
import inspect
import logging
import OpenSSL
import os
import random
import shutil
import socket
import ssl
import struct
import tempfile
import traceback
import twisted.internet.ssl

from twisted.internet.ssl import CertificateOptions, trustRootFromCertificates


class Options(CertificateOptions):
    def __init__(self, owner, trust=None, **kwds):
        super().__init__(
            privateKey=owner['pair'].privateKey.original,
            certificate=owner['pair'].original,
            trustRoot=trust,
            **kwds,
        )
        self.__owner = owner
        self.__trust = trust

    def getContext(self):
        self.certificate = self.__owner['pair'].cert.original
        self.privateKey = self.__owner['pair'].privateKey.original
        if self.__trust is not None:
            self.trustRoot = trustRootFromCertificates([self.__trust['root']])
        return super().getContext()


_guests = {}
_myself = {}
_system = {}
_trust = {}
_log = logging.getLogger(__name__)
_PGP = None
gpgargname = (
    'gnupghome'
    if 'gnupghome' in inspect.signature(gnupg.GPG).parameters
    else 'homedir'
)

AccessLevel = enum.Enum('AccessLevel', ['protected', 'private', 'public'])


class TwistedWrapper:
    # pylint: disable=too-few-public-methods
    def __init__(self, protocol, address):
        self.__address = address
        self.__buf = b''
        self.__dr = None
        self.__len = 4
        self.__msg = ''
        self.__phase = self._p1
        self.__p = protocol

        if address and 0 < dir(protocol).count('dataReceived'):
            self.__dr = getattr(protocol, 'dataReceived')
            setattr(protocol, 'dataReceived', self.process)
            pass
        return

    def _len(self):
        return self.__len

    def _phase(self):
        return self.__phase

    def _p1(self, data: bytes) -> bool:
        _log.debug('pi: %s', str(self.__address))
        result = struct.unpack('>I', data)[0] == 4
        self.__phase = self._p2
        return result

    def _p2(self, data: bytes) -> bool:
        _log.debug('p2: %s', str(self.__address))
        self.__len = struct.unpack('>I', data)[0]
        self.__phase = self._p3
        return True

    def _p3(self, hid: bytes) -> bool:
        _log.debug('p3: %s', str(self.__address))
        response = _PGP.verify(hid)

        if response.valid:
            hid = _PGP.decrypt(hid).data.decode()
            _log.debug('Received handshake identification:\n%s', hid)
            self.__msg = 'timestamp: ' + str(
                datetime.datetime.now(datetime.UTC)
            )
            self.__msg += '\nunique id: ' + str(random.random())
            msg = struct.pack('>I', len(self.__msg)) + self.__msg.encode()

            if isinstance(self.__p, socket.socket):
                self.__p.sendall(msg)
            else:
                self.__p.transport.write(msg)

            self.__len = 8
            self.__phase = self._p4
            pass
        return response.valid

    def _p4(self, data: bytes) -> bool:
        _log.debug('p4: %s', str(self.__address))
        lens = struct.unpack('>II', data)
        self.__len = lens[1]
        self.__phase = self._p5
        return lens[0] == 4

    def _p5(self, reply: bytes) -> bool:
        _log.debug('p5: %s', str(self.__address))
        response = _PGP.verify(reply)

        if response.valid:
            reply = _PGP.decrypt(reply).data.decode()
            response.valid = reply.strip() == self.__msg.strip()

            if not response.valid:
                _log.warning(
                    'Did not echo my message. Expectation: "%s" but received this "%s".',
                    self.__msg.strip(),
                    reply.strip(),
                )
                pass
            pass
        if response.valid and self.__dr is not None:
            setattr(self.__p, 'dataReceived', self.__dr)
            self.__dr(self.__buf)
            self.__buf = b''
            pass
        if response.valid:
            _log.debug('handshake was successful')

        self.__phase = self._p6
        return response.valid

    @staticmethod
    def _p6(_ignore: bytes) -> bool:
        return False

    def process(self, data: bytes) -> None:
        self.__buf += data

        while self.__len <= len(self.__buf):
            data = self.__buf[: self.__len]
            self.__buf = self.__buf[self.__len :]

            if not self.__phase(data):
                _log.error(
                    'failed to pass handshake at %s of %s. Killing the connection to %s.',
                    self.__phase.__name__,
                    str(type(self.__p)),
                    str(self.__address),
                )
                self.__p.transport.loseConnection()
                self.__len = len(self.__buf) + 1  # break out of the while loop
                pass
            pass
        return

    pass


def _my_ip() -> str:
    # pylint: disable=bare-except
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(
            ('8.8.8.8', 0)
        )  # connecting to a UDP address doesn't send packets
        response = s.getsockname()[0]
    except:  # noqa: E722
        print('failed to get host name falling back to localhost')
        traceback.print_exc()
        response = 'localhost'
        pass
    return response


def _recv(s: socket.socket) -> str:
    length = struct.unpack('>I', s.recv(4))[0]
    return s.recv(length)


def _send(s: socket.socket, message: str):
    signed = _PGP.sign(message, passphrase='1234567890', clearsign=True)

    # signed.data is dynamic so pylint: disable=no-member
    if signed.data:
        s.sendall(
            struct.pack('>I', 4)
            + struct.pack('>I', len(signed.data))
            + signed.data
        )
    else:
        _log.error(signed.status)
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        pass
    return


def connect(address: (str, int)) -> socket.socket:
    '''connect using PGP handshaking'''
    s = socket.socket()

    try:
        if use_tls():
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.load_verify_locations(_myself['file'])
            context.load_cert_chain(_myself['file'])
            ss = context.wrap_socket(s, server_hostname=address[0])
            ss.connect(address)
            return ss

        s.connect(address)
        message = ' machine: ' + _my_ip() + '\n'
        message += (
            'temporal: ' + str(datetime.datetime.now(datetime.UTC)) + '\n'
        )
        message += 'username: ' + getpass.getuser() + '\n'
        _send(s, message)
        _send(s, _recv(s))
        return s
    # catch all exceptions (bare) to log a message for address resolution
    # then continue raising the same eception, which makes catching bare
    # exception just fine
    except:  # fmt: skip # noqa: E722 # pylint: disable=bare-except
        _log.exception(
            'Could not connect to %s:%s because',
            str(address[0]),
            str(address[1]),
        )
        raise


def delete(keys: [str]) -> None:
    _PGP.delete_keys('\n'.join(keys))


def extend(keys: [str]) -> None:
    return _PGP.import_keys('\n'.join(keys))


def finalize() -> None:
    '''clean up after ones self

    Should be called when all done with the security module.
    '''
    shutil.rmtree(getattr(_PGP, gpgargname), ignore_errors=True)
    return


def initialize(
    path: str = None,
    myauth: str = None,
    myname: str = None,
    myself: str = None,
    system: str = None,
) -> None:
    '''initialie this library with the PGP keyring location and TLS certificates

    Load both PGP and TLS to be backward compatible.
    '''
    _pgp_initialize(path)
    _tls_initialize(path, myauth, myname, myself, system)
    return


def _pgp_initialize(path: str = None) -> None:
    '''initialize this library with the PGP keyring location

    An empty or None path indicates that we should ignore PGP key verification.
    Rather than have the user maintain a set of keyrings, just have gnuPG use
    a temp directory for the keyring, then import the public an secret keys
    from a directory like `.ssh`.

    File pattern for locating the keys is ...

    path  : path to find the PGP keys dawgie.*.{pub,sec}

    '''
    # cannot call logging from here because we are trying to start it
    print('PGP support is deprecated and will be removed')

    # pylint: disable=import-outside-toplevel,import-self,protected-access
    import dawgie.security

    dawgie.security._PGP = gnupg.GPG(**{gpgargname: tempfile.mkdtemp()})

    if path and os.path.exists(path) and os.path.isdir(path):
        keys = []
        for fn in filter(
            lambda fn: fn.startswith('dawgie.')
            and (fn.endswith('.pub') or fn.endswith('.sec')),
            os.listdir(path),
        ):
            with open(os.path.join(path, fn), 'rt', encoding="utf-8") as f:
                keys.append(f.read())
            pass

        if keys:
            keys = _PGP.import_keys('\n'.join(keys))
        else:
            _log.warning(
                'No PGP keys found for secure handshake in %s', str(path)
            )
        pass
    return


def _grant_access():
    '''scan the path given at initialization time for acceptible keys'''
    certs = []
    path = _guests['path']
    for fn in filter(
        lambda fn: fn.startswith('signed.public.pem'), os.listdir(path)
    ):
        _log.info('Found public key file: %s', fn)
        with open(os.path.join(path, fn), 'rt', encoding='utf-8') as file:
            cert = twisted.internet.ssl.Certificate.loadPEM(file.read())
        if _verified_by_ca(cert, _trust['root']):
            certs.append(cert)
            _log.info('Adding client cert: %s', fn)
        else:
            _log.warning('Ignoring guest cert %s: not signed by CA', fn)
    # FUTURE: add check if not certs then raise ValueError()
    if not certs:
        _log.warning('No TLS kes found for secure clients in %s', path)
    _guests['certs'] = certs


def _pub_certs(cxt: str):
    '''helper function to get more than one cert from a PEM'''
    pub = []
    bdx = cxt.find('-----BEGIN CERTIFICATE-----')
    while bdx > 0:
        edx = cxt.find('-----END CERTIFICATE-----', bdx) + 25
        pub.append(twisted.internet.ssl.Certificate.loadPEM(cxt[bdx:edx]))
        bdx = cxt.find('-----BEGIN CERTIFICATE-----', edx)
    return pub


def _reload(pem):
    '''reload from the same file PEM information'''
    with open(pem['file'], 'rt', encoding='utf-8') as file:
        cxt = file.read()
    if 'pair' in pem and 'root' in pem:
        pem['pair'] = twisted.internet.ssl.PrivateCertificate.loadPEM(cxt)
        pem['root'] = _pub_certs(cxt)
    elif 'pair' in pem:
        pem['pair'] = twisted.internet.ssl.PrivateCertificate.loadPEM(cxt)
    elif 'root' in pem:
        pem['root'] = twisted.internet.ssl.Certificate.loadPEM(cxt)


def _tls_initialize(
    path: str = None,
    myauth: str = None,
    myname: str = None,
    myself: str = None,
    system: str = None,
) -> None:
    '''initialize this library with the TLS certificates

    An empty or None path indicates that we should ignore TLS certificates.
    Rather than have the user maintain a set of certificates, allow anyone and
    everyone access.

    path   : path to find the PGP keys signed.public.pem*
    myauth : CA for myself and guests
    myname : the host name in the certificate
    myself : absolute file path a private certificate PEM that contains the
             private key and a single certificate.
    system : should be dawgie.conext.ssl_pem_file
    '''
    _guests.clear()
    _myself.clear()
    _system.clear()
    _trust.clear()
    if myauth and os.path.isfile(myauth):
        _trust['file'] = myauth
        _trust['root'] = None
        _reload(_trust)
    else:
        _log.warning(
            'No CA found at %s; guest certs cannot be verified and will be '
            'ignored, myself will be accepted unverified',
            myauth,
        )
    if system and os.path.isfile(system):
        _system['file'] = system
        _system['pair'] = None
        _reload(_system)
    else:
        _log.warning(
            'No system wide certificate given the HTTPS service. '
            'Will attempt to fall back to using myself if available. '
            'Otherwise, will have to fall back to just HTTP and open sockets.'
        )
    if myself:
        _myself.update(
            {'file': myself, 'name': myname, 'pair': None, 'root': None}
        )
        _reload(_myself)
    else:
        _log.warning('Really should define myself as a self-signed cert.')
    if _trust and path and os.path.exists(path) and os.path.isdir(path):
        _guests['path'] = path
        _grant_access()
    else:
        _log.warning('No guests allowed.')
    return


def _verified_by_ca(
    cert: twisted.internet.ssl.Certificate, ca: twisted.internet.ssl.Certificate
) -> bool:
    '''return True if cert was signed by ca'''
    store = OpenSSL.crypto.X509Store()
    store.add_cert(ca.original)
    ctx = OpenSSL.crypto.X509StoreContext(store, cert.original)
    try:
        ctx.verify_certificate()
        return True
    except OpenSSL.crypto.X509StoreContextError as e:
        _log.warning('certificate not signed by CA: %s', e)
        return False


def pgp():
    return _PGP


def _lookup(fullname: str):
    name = fullname.split('.')
    modname = '.'.join(name[:-1])
    fncname = name[-1]
    mod = importlib.import_module(modname)
    return getattr(mod, fncname)


def clients() -> [twisted.internet.ssl.Certificate]:
    return _guests.copy()


def fetch_identity(cert: twisted.internet.ssl.Certificate):
    '''fetch a meaningful identity from the certificate

    The defalt case is simple to return the serial number. DAQGIE does not use
    this value but does pass it down to dawgie.db.view() and then to the AE
    implementations for StateVector.view(). Therefore, any AE that wants to use
    this value should override the default case and return something meaningful
    to itself.

    Empty string is returned if no meaningful identity could be fetched from the
    given certificate or the certificate is None. In essence, the empty string is
    the anonymous or blank identity.
    '''
    return hex(cert.get_serial_number()) if cert else ''


def identity(of_cert: twisted.internet.ssl.Certificate):
    # avoiding circles, pylint: disable=import-outside-toplevel
    import dawgie.context

    try:
        return _lookup(dawgie.context.identity_override)(of_cert)
    except:  # all exceptions are equal, pylint: disable=bare-except # noqa: E722
        _log.exception(
            'Could not translate certificate to any response. '
            'Defaulting to anonymous.'
        )
    return ''


def is_sanctioned(
    endpoint: str, cert: twisted.internet.ssl.Certificate
) -> bool:
    '''determine if access to the endpoint is sectioned

    endpoint : string representation of the endpoint being evoked
    cert : the client certificate if there is one - None means anonymous

    Try for simplicity in that if no clients are given, then all endpoints
    are accessable. Yes, this can be a security leak but that should be resolved
    when the PGP is removed and no client TLS certs causes an error.
    '''
    if clients():
        all_access = [
            # 3.0.0 remove - endpoints from here
            '/app/db/item',
            '/app/db/lockview',
            '/app/db/prime',
            '/app/db/targets',
            '/app/db/versions',
            '/app/pl/log',
            '/app/pl/state',
            '/app/schedule/crew',
            '/app/schedule/doing',
            '/app/schedule/events',
            '/app/schedule/failure',
            '/app/schedule/success',
            '/app/schedule/tasks',
            '/app/schedule/todo',
            '/app/search/completion/sv',
            '/app/search/completion/tn',
            '/app/filter/admin',
            '/app/filter/dev',
            '/app/filter/user',
            '/app/search/ri',
            '/app/search/sv',
            '/app/search/tn',
            '/app/changeset.txt',
            '/app/state/status',
            '/app/versions',
            # 3.0.0 remove - to here
            '/api/ae/name',
            '/api/cmd/revision',
            # '/api/cmd/reset',  # should require client cert (trusted)
            # '/api/cmd/run',  # should require client cert (any)
            # '/api/cmd/snapshot',  # should require client cert (admin)
            # '/api/cmd/submit',  # should require client cert (any)
            '/api/database/runid/max',
            '/api/database/runnables',
            '/api/database/search',
            '/api/database/filter/target',
            '/api/database/filter/task',
            '/api/database/filter/alg',
            '/api/database/filter/sv',
            '/api/database/targets',
            '/api/database/view',
            '/api/df_model/statistics',
            '/api/logs/recent',
            '/api/pipeline/state',
            '/api/schedule/doing',
            '/api/schedule/events',
            '/api/schedule/failed',
            '/api/schedule/in-progress',
            '/api/schedule/invalid',
            '/api/schedule/stats',
            '/api/schedule/succeeded',
            '/api/schedule/to-do',
        ]
        if cert is None and endpoint in all_access:
            return True
        if cert is None:
            return False
        return True
    return True


def options(
    owner: AccessLevel, trust: AccessLevel = None
) -> CertificateOptions:
    '''create a mutatable options to support reload

    owner:
      public/protected - return system if present otherwise myself
      private - return myself (mutual TLS)

    trust:
      public - throw an error because cannot trust the public
      protected - use system if present otherwise myself
      private - myself only (mutual TLS)
    '''
    match owner:
        case AccessLevel.public | AccessLevel.protected:
            own = _system if _system else _myself
        case AccessLevel.private:
            own = _myself

    # mutual TLS pinned to our own cert only -- a peer must present
    # this exact self-signed cert back to connect. blocks any other
    # process (dev, prod, whatever) that doesn't hold this file.
    match trust:
        case AccessLevel.private:
            root = _myself
        case AccessLevel.protected:
            root = _trust if _trust else _myself
        case AccessLevel.public:
            raise ValueError('public acess does not require a trust root')
        case None:
            root = None
    return Options(own, root)


def reload(
    ca: bool = False,
    guests: bool = False,
    myself: bool = False,
    system: bool = False,
):
    result = []
    if ca and _trust:
        _reload(_trust)
        result.append('CA')
    if system and _system:
        _reload(_system)
        result.append('system PEM')
    if myself and _myself:
        _reload(_myself)
        result.append('myself PEM')
    if guests and _guests:
        _grant_access()
        result.append('guest CERTs')


def sanctioned(endpoint: str, cert: twisted.internet.ssl.Certificate) -> bool:
    # avoiding circles, pylint: disable=import-outside-toplevel
    import dawgie.context

    try:
        return _lookup(dawgie.context.sanction_override)(endpoint, cert)
    except:  # all exceptions are equal, pylint: disable=bare-except # noqa: E722
        _log.exception(
            'Could not determine if endpoint is sanctioned. '
            'Defaulting to False.'
        )
    return False


def use_client_verification():
    return bool(_guests)


def use_tls():
    return bool(_myself)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(
        description='When run as a standalone tool, it used to generate keys for DAWGIE users. The public key generated here should be placed in the DAWGIE OPS gpg home directory and the secret key should go the DAWGIE user gpg home directory. In both cases, they should be -rw------- in that directory. If the DAWGIE loses control of private key, the public should be removed from the DAWGIE gpg home directory. The removal of the public key is equivalent to revoking the key.'
    )
    ap.add_argument(
        '-e',
        '--user-email',
        required=True,
        help='real email to contact the user',
    )
    ap.add_argument(
        '-O',
        '--output-dir',
        required=True,
        help='deposit the new keys in the given directory',
    )
    ap.add_argument(
        '-u',
        '--user-name',
        required=True,
        help='real name in the form "First Last"',
    )
    args = ap.parse_args()
    homedir = tempfile.mkdtemp()
    gpg = gnupg.GPG(**{gpgargname: homedir})
    k = gpg.gen_key(
        gpg.gen_key_input(
            key_type='DSA', name_email=args.user_email, name_real=args.user_name
        )
    )
    bn = os.path.join(args.output_dir, 'dawgie.%s.%s')
    with open(bn % (args.user_name, 'pub'), 'tw', encoding="utf-8") as gf:
        gf.write(gpg.export_keys(k))
    with open(bn % (args.user_name, 'sec'), 'tw', encoding="utf-8") as gf:
        gf.write(gpg.export_keys(k, True))
    os.chmod(bn % (args.user_name, 'pub'), 0o600)
    os.chmod(bn % (args.user_name, 'sec'), 0o600)
    shutil.rmtree(homedir)
    pass
