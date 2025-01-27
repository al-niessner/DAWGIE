'''Built-in Front-End for DAWGIE

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

import dawgie.context
import dawgie.pl.state
import dawgie.fe
import dawgie.security
import twisted.internet
import twisted.web.resource
import twisted.web.server

dawgie.context.fsm = dawgie.pl.state.FSM()
dawgie.security.initialize(
    path=dawgie.context.guest_public_keys,
    myname=dawgie.context.ssl_pem_myname,
    myself=dawgie.context.ssl_pem_myself,
    system=dawgie.context.ssl_pem_file,
)
factory = twisted.web.server.Site(dawgie.fe.root())

if dawgie.security.use_tls():
    cert = dawgie.security.authority()
    twisted.internet.reactor.listenSSL(
        dawgie.context.fe_port, factory, cert.options()
    )
    if dawgie.security.clients():
        twisted.internet.reactor.listenSSL(
            dawgie.context.cfe_port,
            factory,
            cert.options(*dawgie.security.clients()),
        )
else:
    twisted.internet.reactor.listenTCP(dawgie.context.fe_port, factory)

twisted.internet.reactor.run()
