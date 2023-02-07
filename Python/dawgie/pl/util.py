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

import logging; log = logging.getLogger(__name__)
import os
import twisted.internet.error
import twisted.internet.protocol
import twisted.internet.reactor

class SVGOHandler(twisted.internet.protocol.ProcessProtocol):
    def __init__ (self, command): self.__command = command
    def processEnded(self, reason):
        if isinstance (reason.value, twisted.internet.error.ProcessTerminated):
            # long statement to log so pylint: disable=logging-not-lazy
            # exceptions always look the same; pylint: disable=duplicate-code
            log.critical ('Error in archiving of data.    EXIT CODE: %s'+
                          '   SIGNAL: %s    STATUS: %s   COMMAND: "%s"',
                          str (reason.value.exitCode),
                          str (reason.value.signal),
                          str (reason.value.status),
                          self.__command)
            pass
        return
    pass

def svgo (ifn, ofn):
    args = ['/usr/lib/node_modules/svgo/bin/svgo', ifn, ofn,
            '--disable=cleanupIDs', '--enable=removeStyleElement']
    handler = SVGOHandler(' '.join (args))
    twisted.internet.reactor.spawnProcess (handler, args[0], args=args,
                                           env=os.environ)
    return
