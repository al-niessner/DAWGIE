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
import dawgie.db
import dawgie.util


def current(factories):
    '''Get the current version numbers from the software'''
    talg = {}
    tsv = {}
    tv = {}
    for f in factories:
        bot = f(dawgie.util.task_name(f))
        for alg in bot.list():
            name = '.'.join([bot._name(), alg.name()])  # fmt: skip # pylint: disable=protected-access
            if name not in talg:
                talg[name] = alg.asstring()

            for sv in alg.state_vectors():
                name = '.'.join([bot._name(), alg.name(), sv.name()])  # fmt: skip # pylint: disable=protected-access
                if sv.keys() and name not in tsv:
                    tsv[name] = sv.asstring()

                for k in sv.keys():
                    name = '.'.join([bot._name(), alg.name(), sv.name(), k])  # fmt: skip # pylint: disable=protected-access
                    if name not in tv:
                        tv[name] = sv[k].asstring()
                    pass
                pass
            pass
        pass
    return talg, tsv, tv


def persistent():
    '''Get the known versions from the database'''
    return dawgie.db.versions()


def record(task, only=None):
    '''Record this version of the software'''
    if isinstance(task, (dawgie.Task, dawgie.Analysis, dawgie.Regress)):
        for alg in filter(
            lambda a: only is None or a.name() == only, task.list()
        ):
            if not alg.state_vectors():
                dawgie.db.update(task, alg, None, None, None)
            for sv in alg.state_vectors():
                for k, v in sv.items():
                    dawgie.db.update(task, alg, sv, k, v)
                pass
            pass
        pass
    return
