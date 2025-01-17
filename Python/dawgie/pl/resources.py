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

HINT = collections.namedtuple(
    'HINT', ['cpu', 'io', 'memory', 'pages', 'summary']
)


def _latest(history: [dawgie.db.MetricData]) -> dawgie.db.MetricData:
    most_recent = history[0]
    for h in history:
        if int(most_recent.run_id) < int(h.run_id):
            most_recent = h
        pass
    return most_recent


def aspects(metric: [dawgie.db.MetricData]) -> {str: [dawgie.db.MetricData]}:
    log.debug('aspects() - metrics of aspects over %d', len(metric))
    reg = regress(metric)
    log.debug('aspects() - number of regressions %d', len(reg))
    names = {'.'.join([m.task, m.alg_name]) for m in metric}
    asp = {name: [] for name in names}
    for r in reg:
        name = '.'.join(r.split('.')[1:])
        asp[name].append(_latest(reg[r]))
        pass
    return asp


def distribution(metric: [dawgie.db.MetricData]) -> {str: HINT}:
    log.debug(
        'distribution() - use metrics for automaated choice of distribution over %d',
        len(metric),
    )
    dst = {}
    reg = regress(metric)
    log.debug('distribution() - number of regressions %d', len(reg))
    for name in reg:
        if reg[name]:
            cpu = numpy.median(
                [
                    m.sv['task_system'].value() + m.sv['task_user'].value()
                    for m in reg[name]
                ]
            )
            io = numpy.median(
                [
                    m.sv['task_input'].value() + m.sv['task_output'].value()
                    for m in reg[name]
                ]
            )
            memory = numpy.median(
                [
                    round(
                        (
                            m.sv['db_memory'].value()
                            + m.sv['task_memory'].value()
                        )
                        / 2**20
                    )
                    for m in reg[name]
                ]
            )
            pages = numpy.median(
                [
                    m.sv['task_pages'].value() + m.sv['task_pages'].value()
                    for m in reg[name]
                ]
            )
            summary = dawgie.context.cpu_threshold <= cpu
        else:
            cpu, io, memory, pages, summary = 0, 0, 0, 0, False

        dst[name] = HINT(cpu, io, memory, pages, dawgie.Distribution(summary))
        pass
    return dst


def regress(metric: [dawgie.db.MetricData]) -> {str: [dawgie.db.MetricData]}:
    log.debug('regress() - regress back across metric data %d', len(metric))
    names = {'.'.join([m.target, m.task, m.alg_name]) for m in metric}
    reg = {name: [] for name in names}
    for m in metric:
        name = '.'.join([m.target, m.task, m.alg_name])
        reg[name].append(m)
        pass
    return reg
