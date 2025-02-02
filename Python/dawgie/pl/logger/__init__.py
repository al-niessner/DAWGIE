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

import logging
import logging.handlers
import os
import pickle
import struct
import twisted.internet.reactor
import twisted.internet.threads

_ROOT = None

# Importing libraries gets complicated so pylint: disable=import-outside-toplevel


class LogFilter(logging.Filter):
    # pylint: disable=too-few-public-methods
    def filter(self, record):
        return not (
            record.name == 'gnupg'
            and record.levelno < logging.ERROR
            and not logging.getLogger().isEnabledFor(logging.DEBUG)
        )

    pass


class LogSink(twisted.internet.protocol.Protocol):
    def __init__(self, actual, address):
        import dawgie.security

        self.__actual = actual
        self.__buf = b''
        self.__blen = len(struct.pack('>L', 0))
        self.__len = None
        if not dawgie.security.use_tls():
            # this is really used so pylint: disable=unused-private-member
            self.__handshake = dawgie.security.TwistedWrapper(self, address)
        return

    def dataReceived(self, data):
        # protocols are independent even if similar today
        # pylint: disable=duplicate-code
        self.__buf += data
        length = self.__blen if self.__len is None else self.__len
        while length <= len(self.__buf):
            if self.__len is None:
                self.__len = struct.unpack('>L', self.__buf[:length])[0]
                self.__buf = self.__buf[length:]
            else:
                record = pickle.loads(self.__buf[:length])
                self.__actual.handle(logging.makeLogRecord(record))
                self.__actual.flush()
                self.__buf = self.__buf[length:]
                self.__len = None
                pass

            length = self.__blen if self.__len is None else self.__len
            pass
        return

    pass


class LogSinkFactory(twisted.internet.protocol.Factory):
    def __init__(self, path):
        # pylint: disable=protected-access
        import dawgie.security

        twisted.internet.protocol.Factory.__init__(self)
        self.__actual = (
            logging.handlers.StreamHandler()
            if path is None
            else logging.handlers.TimedRotatingFileHandler(
                path,
                backupCount=dawgie.context.log_backup,
                when='midnight',
                utc=True,
            )
        )
        self.__actual.addFilter(LogFilter('gnupg'))
        self.__actual.setFormatter(
            logging.Formatter(
                '%(asctime)s :: '
                + '%(name)s :: '
                + '%(levelname)s :: '
                + '%(message)s'
            )
        )
        self.__host = dawgie.security._my_ip()
        self.__pid = os.getpid()
        return

    def actual(self):
        return self.__actual

    def buildProtocol(self, addr):
        return LogSink(self.__actual, addr)

    def isWithinReactor(self):  # pylint: disable=invalid-name
        import dawgie.security

        # pylint: disable=protected-access
        return (
            self.__host == dawgie.security._my_ip()
            and self.__pid == os.getpid()
        )

    pass


class TwistedHandler(logging.handlers.SocketHandler):
    def __init__(self, *args, **kwds):
        logging.handlers.SocketHandler.__init__(self, *args, **kwds)
        self.__shaking = False
        self.__q = []
        pass

    def emit(self, record):
        if _ROOT is not None and _ROOT.isWithinReactor():
            _ROOT.actual().handle(record)
        else:
            if self.__shaking:
                self.__q.append(record)
            else:
                for r in self.__q:
                    super().emit(r)
                self.__q = []
                super().emit(record)
                pass
            pass
        return

    def makeSocket(self, timeout=1):
        import dawgie.security

        self.__shaking = True
        s = dawgie.security.connect(self.address)
        self.__shaking = False
        return s

    pass


def start(path: str, port: int) -> None:
    # pylint: disable=import-self,protected-access
    import dawgie.context
    import dawgie.pl.logger

    dawgie.pl.logger._ROOT = LogSinkFactory(path)
    if dawgie.security.use_tls():
        controller = dawgie.security.authority().options(
            *dawgie.security.certificates()
        )
        twisted.internet.reactor.listenSSL(
            port,
            dawgie.pl.logger._ROOT,
            controller,
            dawgie.context.worker_backlog,
        )
    else:
        # cannot call logging from here because we are trying to start it
        print('PGP support is deprecated and will be removed')
        twisted.internet.reactor.listenTCP(
            port, dawgie.pl.logger._ROOT, dawgie.context.worker_backlog
        )
    return
