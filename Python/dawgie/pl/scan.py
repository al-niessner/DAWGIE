'''
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

import dawgie
import dawgie.base
import dawgie.context
import logging
import importlib
import os
import pkgutil

IGNORE = []
LOG = logging.getLogger(__name__)
REGISTRY = {}


def _register(cls=None):
    ae_pkg = dawgie.context.ae_base_package
    tn_loc = len(ae_pkg.split('.'))
    if cls is None:
        REGISTRY['deprecated call'] = True
    else:
        tn = cls.__module__.split('.')[tn_loc]
        if getattr(cls, 'DAWGIE_IGNORE', False):
            pass
        elif tn not in REGISTRY:
            REGISTRY[tn] = dawgie.base.Factories(tn).add(cls)
        elif REGISTRY[tn]:
            REGISTRY[tn].add(cls)


def advanced_factories(ae, pkg):
    REGISTRY.clear()
    attrname = '_master_registry'
    factories = {e: [] for e in dawgie.Factories}
    orignal = getattr(dawgie, attrname)
    setattr(dawgie, attrname, _register)
    try:
        for modinfo in pkgutil.walk_packages([ae], pkg + '.'):
            if not any(modinfo.name.startswith(ignore) for ignore in IGNORE):
                m = importlib.import_module(modinfo.name)
                if getattr(m, 'DAWGIE_IGNORE', False):
                    IGNORE.append(modinfo.name)
        if 'deprecated call' in REGISTRY:
            REGISTRY.clear()
            factories.clear()
    finally:
        setattr(dawgie, attrname, orignal)
    for tn, fs in REGISTRY.items():
        m = importlib.import_module('.'.join([pkg, tn]))
        for f in dawgie.Factories:
            # This implementation allows users to override the factory/bot
            # pattern by defining their own factory functions at the task level
            # module. By utilizing dawgie.base classes directly along with their
            # factory functions, users can customize behavior without resorting
            # to monkey patching. While the scanner will still detect all their
            # Algorithm/Analyzer/Regression classes, this redundancy is an
            # acceptable trade-off for a cleaner extension API.
            fn = f.name
            if hasattr(m, fn):
                LOG.warning(
                    'the module %s already contains the attribute %s. '
                    'Not overriding it.',
                    m.__name__,
                    fn,
                )
            else:
                setattr(m, fn, getattr(fs, fn))
            if f == dawgie.Factories.events:
                something = getattr(m, fn)()
            else:
                something = getattr(m, fn)().routines()
            if something:
                factories[f].append(getattr(m, fn))
    return factories


def deprecated_factories(ae, pkg):
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
            LOG.warning('Ignoring package: %s', fp)
            continue

        LOG.info('Working on module %s', fp)

        if not any((e.name in dm for e in dawgie.Factories)):
            LOG.error(
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
        LOG.info('%s: %d', e.name, len(factories[e]))
    return factories


def for_factories(ae, pkg):
    result = advanced_factories(ae, pkg)
    if not result:
        LOG.critical(
            'The older factory/bot/alg pattern has been deprecated and is slated to be removed.'
        )
        result = deprecated_factories(ae, pkg)
    return result
