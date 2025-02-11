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
import logging; log = logging.getLogger(__name__)  # fmt: skip # noqa: E702 # pylint: disable=multiple-statements
import importlib
import os


def for_factories(ae, pkg):
    factories = {e: [] for e in dawgie.Factories}
    for pkg_name in filter(
        lambda fn: os.path.isdir(os.path.join(ae, fn)) and fn != '__pycache__',
        os.listdir(ae),
    ):
        fp = '.'.join([pkg, pkg_name])
        mod = importlib.import_module(fp)
        dm = dir(mod)
        ignore = any(
            [
                (
                    getattr(mod, 'dawgie_ignore')
                    if 'dawgie_ignore' in dm
                    else False
                ),
                (
                    getattr(mod, 'DAWGIE_IGNORE')
                    if 'DAWGIE_IGNORE' in dm
                    else False
                ),
            ]
        )

        if ignore:
            log.warning('Ignoring package: %s', fp)
            continue

        log.info('Working on module %s', fp)

        if not any((e.name in dm for e in dawgie.Factories)):
            log.error(
                'The directory %s %s %s %s',
                os.path.join(ae, pkg_name),
                'does not conform to the architecture and design.',
                'It must have at least one analysis, events,',
                'regression, or task factory. Ignoring the package.',
            )
            continue

        for e in dawgie.Factories:
            if e.name in dm:
                factories[e].append(getattr(mod, e.name))
            pass
        pass
    for e in dawgie.Factories:
        log.info('%s: %d', e.name, len(factories[e]))
    return factories
