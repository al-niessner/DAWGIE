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

import dawgie
import dawgie.pl.worker
import importlib
import logging; log = logging.getLogger(__name__)  # fmt: skip # noqa: E702 # pylint: disable=multiple-statements
import signal


def _die(signum):
    if signum == signal.SIGABRT:
        raise dawgie.AbortAEError('OS signaled an abort')
    return


def execute(address: (str, int), inc: int, ps_hint: int, rev: str):
    signal.signal(signal.SIGABRT, _die)
    s = dawgie.security.connect(address)
    m = dawgie.pl.message.make(
        typ=dawgie.pl.message.Type.register, inc=inc, rev=rev
    )
    dawgie.pl.message.send(m, s)
    m = dawgie.pl.message.make(typ=dawgie.pl.message.Type.wait)
    while m.type == dawgie.pl.message.Type.wait:
        m = dawgie.pl.message.receive(s)
        pass
    s.close()
    ctxt = dawgie.pl.worker.Context(address, rev)

    if m.type == dawgie.pl.message.Type.task:
        # pylint: disable=bare-except
        if m.ps_hint is not None:
            ps_hint = m.ps_hint

        dawgie.context.loads(m.context)
        dawgie.db.reopen()
        handler = dawgie.pl.logger.TwistedHandler(
            host=address[0], port=dawgie.context.log_port
        )
        logging.basicConfig(handlers=[handler], level=dawgie.context.log_level)
        logging.captureWarnings(True)
        try:
            factory = getattr(
                importlib.import_module(m.factory[0]), m.factory[1]
            )
            nv = ctxt.run(
                factory, ps_hint, m.jobid, m.runid, m.target, m.timing
            )
            # protocols are independent even if similar today
            # pylint: disable=duplicate-code
            m = dawgie.pl.message.make(
                typ=dawgie.pl.message.Type.response,
                inc=m.target,
                jid=m.jobid,
                rid=m.runid,
                suc=True,
                tim=m.timing,
                val=nv,
            )
        except (dawgie.NoValidInputDataError, dawgie.NoValidOutputDataError):
            logging.getLogger(__name__).info(
                'Job "%s" had invalid data for run id %s and target "%s"',
                str(m.jobid),
                str(m.runid),
                str(m.target),
            )
            m = dawgie.pl.message.make(
                typ=dawgie.pl.message.Type.response,
                inc=m.target,
                jid=m.jobid,
                rid=m.runid,
                suc=None,
                tim=m.timing,
            )
        except:  # noqa: E722
            logging.getLogger(__name__).exception(
                'Job "%s" failed to execute successfully for run id %s and target "%s"',
                str(m.jobid),
                str(m.runid),
                str(m.target),
            )
            m = dawgie.pl.message.make(
                typ=dawgie.pl.message.Type.response,
                inc=m.target,
                jid=m.jobid,
                rid=m.runid,
                suc=False,
                tim=m.timing,
            )
        finally:
            dawgie.db.close()
            s = dawgie.security.connect(address)
            if not ctxt.abort():
                dawgie.pl.message.send(m, s)
            pass
    elif m.type == dawgie.pl.message.Type.response and not m.success:
        raise ValueError('Not the same software revisions!')
    else:
        raise ValueError('Wrong message type: ' + str(m.type))
    return
