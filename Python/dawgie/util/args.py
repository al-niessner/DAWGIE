'''Argument helpers for the CLI

--
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

NTR: 49811
'''

import dawgie.context

# needed for eval in log_level(); pylint: disable=unused-import
import logging  # noqa: F401

# pylint: enable=unused-import


def log_level(level):
    """Allow log level to be symbolic or a plain integer"""
    # pylint: disable=bare-except,eval-used
    try:
        ll = int(level)
    except:  # noqa: E722
        ll = eval(level)
    return ll


def set_ports(fe_port: int) -> None:
    fep = int(fe_port)
    dawgie.context.cfe_port = fep + dawgie.context.PortOffset.certFE.value
    dawgie.context.cloud_port = fep + dawgie.context.PortOffset.cloud.value
    dawgie.context.db_port = fep + dawgie.context.PortOffset.shelve.value
    dawgie.context.farm_port = fep + dawgie.context.PortOffset.farm.value
    dawgie.context.fe_port = fep + dawgie.context.PortOffset.frontend.value
    dawgie.context.log_port = fep + dawgie.context.PortOffset.log.value
    return
