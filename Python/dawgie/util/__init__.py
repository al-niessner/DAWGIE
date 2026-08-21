'''Common utilities for the pipeline

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

NTR: 49811
'''

from .args import log_level, resolve_security_args, set_ports
from .metrics import MetricStateVector, MetricValue
from .names import task_module, task_name, verify_name
from .refs import algref2svref, as_vref, svref2vref, vref_as_name

# 3.0.0 remove - get rid of resolve_site() and all that calls to it
import dawgie.context
import logging
import os
from importlib.resources import files
from pathlib import Path

LOG = logging.getLogger(__name__)


def resolve_site() -> (Path, bool):
    sdir = dawgie.context.site_path
    isdep = False
    if sdir and not os.path.isdir(sdir):
        LOG.error('the UI path %s does not exist', sdir)
        sdir = ''
    if not sdir:
        LOG.warning('using deprecated UI')
        sdir = (files('dawgie.fe') / 'deprecated').resolve()
        isdep = True
    else:
        sdir = Path(sdir).resolve()
    return sdir, isdep


__all__ = [
    'MetricStateVector',
    'MetricValue',
    'algref2svref',
    'as_vref',
    'log_level',
    'resolve_security_args',
    'resolve_site',
    'set_ports',
    'svref2vref',
    'task_module',
    'task_name',
    'verify_name',
    'vref_as_name',
]
