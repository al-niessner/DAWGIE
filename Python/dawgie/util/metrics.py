'''Metric helpers

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

import dawgie


class MetricStateVector(dawgie.StateVector):
    def __init__(self, db: dawgie.METRIC, task: dawgie.METRIC):
        dawgie.StateVector.__init__(self)
        self.units = {
            'input': ' (block)',
            'memory': ' (Kbytes)',
            'output': ' (block)',
            'pages': ' (page)',
            'system': ' (s)',
            'user': ' (s)',
            'wall': ' (s)',
        }
        self._version_ = dawgie.VERSION(1, 1, 1)
        self['db_input'] = MetricValue(db.input)
        self['db_memory'] = MetricValue(db.mem)
        self['db_output'] = MetricValue(db.output)
        self['db_pages'] = MetricValue(db.pages)
        self['db_system'] = MetricValue(db.sys)
        self['db_user'] = MetricValue(db.user)
        self['db_wall'] = MetricValue(db.wall)
        self['task_input'] = MetricValue(task.input)
        self['task_memory'] = MetricValue(task.mem)
        self['task_output'] = MetricValue(task.output)
        self['task_pages'] = MetricValue(task.pages)
        self['task_system'] = MetricValue(task.sys)
        self['task_user'] = MetricValue(task.user)
        self['task_wall'] = MetricValue(task.wall)
        return

    def name(self):
        return '__metric__'

    def view(self, _caller, visitor: dawgie.Visitor) -> None:
        table = visitor.add_table(
            ['', 'DB', 'Task'], rows=len(self) // 2, title='Process Metrics'
        )
        for r, k in enumerate(
            sorted(filter(lambda k: k.startswith('db_'), self))
        ):
            k = k.split('_')[1]
            table.get_cell(r, 0).add_primitive(
                k + (' (undefined)' if k not in self.units else self.units[k])
            )
            table.get_cell(r, 1).add_primitive(self['db_' + k].value())
            table.get_cell(r, 2).add_primitive(self['task_' + k].value())
            pass
        return

    pass


class MetricValue(dawgie.Value):
    def __init__(self, content=None):
        dawgie.Value.__init__(self)
        self.__content = content
        self._version_ = dawgie.VERSION(1, 1, 0)
        return

    def features(self) -> [dawgie.Feature]:
        return []

    def value(self):
        return self.__content

    pass


def filled(value: int = 0) -> dawgie.METRIC:
    '''create and fill a dawgie.METRIC with given value'''
    return dawgie.METRIC(
        input=value,
        mem=value,
        output=value,
        pages=value,
        sys=value,
        user=value,
        wall=value,
    )
