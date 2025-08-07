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

import collections
import dawgie
import dawgie.context
import dawgie.db
import logging; log = logging.getLogger(__name__)  # fmt: skip # noqa: E702 # pylint: disable=multiple-statements
import numpy
import os
import pickle

HINT = collections.namedtuple(
    'HINT', ['cpu', 'io', 'memory', 'pages', 'summary']
)


def _read_diary():
    fn = os.path.join(dawgie.context.data_per, 'diary.pkl')
    past = {}
    if os.path.isfile(fn):
        with open(fn, 'br') as file:
            past = pickle.load(file)
        # make sure loaded context is an expected structure
        if isinstance(past, dict) and all(
            isinstance(k, str) and isinstance(v, dict) for k, v in past.items()
        ):
            for timelines in past.values():
                if not all(
                    isinstance(k, dict) and isinstance(v, (list, set))
                    for k, v in timelines.items()
                ):
                    past = {}
                    break
        else:
            past = {}
    return past


def _write_diary(known):
    fn = os.path.join(dawgie.context.data_per, 'diary.pkl')
    if os.path.isdir(dawgie.context.data_per):
        with open(fn, 'bw') as file:
            pickle.dump(known, file)


def distribution(metric: [dawgie.db.MetricData]) -> {str: HINT}:
    log.debug(
        'distribution() - use metrics for automaated choice of distribution over %d',
        len(metric),
    )
    dst = {}
    reg = regress(metric)
    log.debug('distribution() - number of regressions %d', len(reg))
    for name, metrics in reg.items():
        if metrics['rids']:
            cpu = numpy.nanmedian(
                numpy.array(metrics['task_system'])
                + numpy.array(metrics['task_user'])
            )
            io = numpy.nanmedian(
                numpy.array(metrics['task_input'])
                + numpy.array(metrics['task_output'])
            )
            memory = numpy.nanmedian(
                (
                    (
                        numpy.array(metrics['db_memory'])
                        + numpy.array(metrics['task_memory'])
                    )
                    / 2**20
                ).round()
            )
            pages = numpy.nanmedian(
                numpy.array(metrics['db_pages'])
                + numpy.array(metrics['task_pages'])
            )
            summary = dawgie.context.cpu_threshold <= cpu
        else:
            cpu, io, memory, pages, summary = 0, 0, 0, 0, False

        dst[name] = HINT(cpu, io, memory, pages, dawgie.Distribution(summary))
        pass
    return dst


def regress(metric: [dawgie.db.MetricData]) -> {str: [dawgie.db.MetricData]}:
    log.debug('regress() - regress back across metric data %d', len(metric))
    keys = [
        'task_system',
        'task_user',
        'task_input',
        'task_output',
        'db_memory',
        'task_memory',
        'db_pages',
        'task_pages',
        'rids',
    ]
    names = {'.'.join([m.target, m.task, m.alg_name]) for m in metric}
    reg = _read_diary()
    reg.update(
        {
            name: {k: set() if k == 'rids' else [] for k in keys}
            for name in names.difference(reg.keys())
        }
    )
    for m in metric:
        name = '.'.join([m.target, m.task, m.alg_name])
        if m.run_id not in reg[name]['rids']:
            reg[name]['rids'].add(m.run_id)
            for vn in keys[:-1]:
                v = m.sv[vn].value()
                if v < 0:
                    v = numpy.nan
                reg[name][vn].append(v)
        pass
    _write_diary(reg)
    return reg
