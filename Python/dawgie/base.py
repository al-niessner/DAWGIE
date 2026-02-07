'''Concrete items that are the heart of dawgie

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

# 3.0.0 remove - this and cleanup code duplication
# pylint: disable=duplicate-code


import datetime
import importlib
import logging
import resource

from dawgie import (
    ALG_REF,
    EVENT,
    METRIC,
    AbortAEError,
    Algorithm,
    Analyzer,
    Dataset,
    Regression,
)
from typing import Self


class _Metric:
    '''Interface used internally to measure process resource usage'''

    def __init__(self):
        self.__history = []
        self.msv = None
        return

    @staticmethod
    def diff(a, b, dt) -> METRIC:
        '''compute a - b'''
        return METRIC(
            input=a.ru_inblock - b.ru_inblock,
            mem=a.ru_maxrss - b.ru_maxrss,
            output=a.ru_oublock - b.ru_oublock,
            pages=a.ru_majflt - b.ru_majflt,
            sys=a.ru_stime - b.ru_stime,
            user=a.ru_utime - b.ru_utime,
            wall=dt,
        )

    def measure(self, func, args=(), ds: 'Dataset' = None):
        c0 = resource.getrusage(resource.RUSAGE_CHILDREN)
        s0 = resource.getrusage(resource.RUSAGE_SELF)
        t0 = datetime.datetime.now(datetime.UTC)
        value = func(*args)
        c1 = resource.getrusage(resource.RUSAGE_CHILDREN)
        s1 = resource.getrusage(resource.RUSAGE_SELF)
        child = _Metric.diff(c1, c0, 0)
        task = _Metric.diff(
            s1, s0, (datetime.datetime.now(datetime.UTC) - t0).total_seconds()
        )
        self.__history.append({'child': child, 'task': task})

        if ds is not None:
            dawgie_util = importlib.import_module('dawgie.util')

            db = ds.sum()
            task = self.sum()
            # internal dawgie work # pylint: disable=protected-access
            ds._update_msv(dawgie_util.MetricStateVector(db, task))
        return value

    def sum(self):
        '''return the sum of all collected metrics'''
        s = METRIC(input=0, mem=0, output=0, pages=0, sys=0.0, user=0.0, wall=0)
        for h in self.__history:
            s = METRIC(
                input=s.input + h['child'].input + h['task'].input,
                mem=s.mem + h['child'].mem + h['task'].mem,
                output=s.output + h['child'].output + h['task'].output,
                pages=s.pages + h['child'].pages + h['task'].pages,
                sys=s.sys + h['child'].sys + h['task'].sys,
                user=s.user + h['child'].user + h['task'].user,
                wall=s.wall + h['child'].wall + h['task'].wall,
            )
        return s

    pass


class Analysis(_Metric):
    '''The Analysis is the base for all bots that analyze data across targets

    Abstract functions that all bots need to implement:

    list() -> return a list of all analyzers
    '''

    def __init__(
        self, name: str, ps_hint: int, runid: int, analyzers: [Analyzer]
    ):
        _Metric.__init__(self)
        self.__analyzers = analyzers
        self.__name = name
        self.__nv = []
        self.__ps_hint = ps_hint
        self.__runid = runid
        self.__timing = {}
        return

    def __repr__(self):
        return '.'.join([str(self.__runid), '__all__', self.__name])

    def _name(self) -> str:
        return self.__name

    def _ps_hint(self) -> int:
        return self.__ps_hint

    def _runid(self) -> int:
        return self.__runid

    def _target(self) -> str:
        return '__all__'

    def abort(self) -> bool:
        '''Check with the pipeline to see if system should abort.

        The default implementation is to always return False. This will allow
        the bots to run in debug mode without modification. However, if in
        computationally expensive AE algorithms, the algorithm can ask the
        bot or itself if it should abort.
        '''
        return False

    def do(self, goto: str = None) -> None:
        dawgie_db = importlib.import_module('dawgie.db')
        log = logging.getLogger(__name__ + '.Analysis')
        for step in filter(
            lambda s: goto is None or s.name() == goto, self.routines()
        ):
            if self.abort():
                raise AbortAEError()

            setattr(step, 'abort', self.abort)
            setattr(step, 'caller', self)
            self.__timing['gather_' + step.name()] = datetime.datetime.now(
                datetime.UTC
            )
            aspect = dawgie_db.gather(step, self)
            self.__timing['collect_' + step.name()] = datetime.datetime.now(
                datetime.UTC
            )
            aspect.collect(step.feedback())
            aspect.collect(step.traits())
            self.__timing['start_' + self._name()] = datetime.datetime.now(
                datetime.UTC
            )
            log.debug('Stepping into %s', step.name())
            self.measure(step.run, args=(aspect,), ds=aspect.ds())
            setattr(step, 'caller', None)
        return

    def routines(self) -> Analyzer:
        return [analyzer() for analyzer in self.__analyzers]

    def new_values(self, value: (str, bool) = None) -> [(str, bool)]:
        if value:
            self.__nv.append(value)
        return self.__nv

    def timing(self):
        return self.__timing

    pass


class Regress(_Metric):
    '''The Regress is the base for all bots that analyze data across runids

    Abstract functions that all bots need to implement:

    list() -> return a list of all analyzers
    '''

    def __init__(
        self, name: str, ps_hint: int, target: str, regressions: [Regression]
    ):
        _Metric.__init__(self)
        self.__name = name
        self.__nv = []
        self.__regressions = regressions
        self.__ps_hint = ps_hint
        self.__target = target
        self.__timing = {}
        return

    def __repr__(self) -> str:
        return '.'.join(['0', self.__target, self.__name])

    def _name(self) -> str:
        return self.__name

    def _ps_hint(self) -> int:
        return self.__ps_hint

    def _runid(self) -> int:
        return 0

    def _target(self) -> str:
        return self.__target

    def abort(self) -> bool:
        '''Check with the pipeline to see if system should abort.

        The default implementation is to always return False. This will allow
        the bots to run in debug mode without modification. However, if in
        computationally expensive AE algorithms, the algorithm can ask the
        bot or itself if it should abort.
        '''
        return False

    def do(self, goto: str = None) -> None:
        dawgie_db = importlib.import_module('dawgie.db')
        log = logging.getLogger(__name__ + '.Regress')
        for step in filter(
            lambda s: goto is None or s.name() == goto, self.routines()
        ):
            if self.abort():
                raise AbortAEError()

            setattr(step, 'abort', self.abort)
            setattr(step, 'caller', self)
            self.__timing['retreat_' + step.name()] = datetime.datetime.now(
                datetime.UTC
            )
            timeline = dawgie_db.retreat(step, self)
            self.__timing['recede_' + step.name()] = datetime.datetime.now(
                datetime.UTC
            )
            timeline.recede(step.feedback())
            timeline.recede(step.variables())
            self.__timing['start_' + self._name()] = datetime.datetime.now(
                datetime.UTC
            )
            log.debug('Stepping into %s', step.name())
            self.measure(
                step.run, args=(self._ps_hint(), timeline), ds=timeline.ds()
            )
            setattr(step, 'caller', None)
        return

    def routines(self) -> [Regression]:
        return [regression() for regression in self.__regressions]

    def new_values(self, value: (str, bool) = None) -> [(str, bool)]:
        if value:
            self.__nv.append(value)
        return self.__nv

    def timing(self):
        return self.__timing

    pass


class Task(_Metric):
    '''The Task is the base class for all bots which are to complete a task

    Abstract functions that all bots need to implement:

    list() -> return a list of all algorithms
    '''

    # Need a lot of information to create this object
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        name: str,
        ps_hint: int,
        runid: int,
        target: str,
        algorithms: [Algorithm],
    ):
        _Metric.__init__(self)
        self.__algorithms = algorithms
        self.__name = name
        self.__nv = []
        self.__ps_hint = ps_hint
        self.__runid = runid
        self.__target = target
        self.__timing = {}

    # pylint: enable=too-many-arguments,too-many-positional-arguments

    def __repr__(self):
        return '.'.join([str(self.__runid), self.__target, self.__name])

    def _make_ds(self, alg) -> Dataset:
        '''Make a Dataset with the minimal help from self.do()'''
        dawgie_db = importlib.import_module('dawgie.db')
        return dawgie_db.connect(alg, self, self.__target)

    def _name(self) -> str:
        return self.__name

    def _ps_hint(self) -> int:
        return self.__ps_hint

    def _runid(self) -> int:
        return self.__runid

    def _target(self) -> str:
        return self.__target

    def abort(self) -> bool:
        '''Check with the pipeline to see if system should abort.

        The default implementation is to always return False. This will allow
        the bots to run in debug mode without modification. However, if in
        computationally expensive AE algorithms, the algorithm can ask the
        bot or itself if it should abort.
        '''
        return False

    def do(self, goto: str = None) -> None:
        log = logging.getLogger(__name__ + '.Task')
        log.debug('Starting %s for %s', self.__name, self._target())
        for step in filter(
            lambda s: goto is None or s.name() == goto, self.routines()
        ):
            if self.abort():
                raise AbortAEError()

            setattr(step, 'abort', self.abort)
            setattr(step, 'caller', self)
            sname = f'{self._target()}.{self._name()}.{step.name()}'
            log.debug('Loading into %s', sname)
            self.__timing['load_' + step.name()] = datetime.datetime.now(
                datetime.UTC
            )
            ds = self._make_ds(step)
            for f in step.feedback():
                ds.load(f)
            for p in step.previous():
                ds.load(p)
            log.debug('Loaded into %s', sname)
            self.__timing[f'start_{step.name()}'] = datetime.datetime.now(
                datetime.UTC
            )
            log.debug('Stepping into %s', sname)
            self.measure(step.run, args=(ds, self._ps_hint()), ds=ds)
            log.debug('Returned from %s', sname)
            setattr(step, 'caller', None)
            pass
        log.debug('Completed %s for %s', self.__name, self._target())
        return

    def routines(self) -> [Algorithm]:
        return [algorithm() for algorithm in self.__algorithms]

    def new_values(self, value: (str, bool) = None) -> [(str, bool)]:
        if value:
            self.__nv.append(value)
        return self.__nv

    def timing(self):
        return self.__timing

    pass


class Factories:
    def __init__(self, name):
        self.__name = name
        self.__algorithms = set()
        self.__analyzers = set()
        self.__events = {}
        self.__regressions = set()

    def __str__(self):
        return f'''
name: {self.__name}
  algorithms:  {len(self.__algorithms)}
  analyzers:   {len(self.__analyzers)}
  events:      {len(self.__events)}
  regressions: {len(self.__regressions)}
'''

    @property
    def name(self):
        return self.__name

    def add(self, cls) -> Self:
        cn = '.'.join([cls.__module__, cls.__qualname__])
        efs = []
        for container, class_type, method in zip(
            [self.__algorithms, self.__analyzers, self.__regressions],
            [Algorithm, Analyzer, Regression],
            [self.task, self.analysis, self.regress],
        ):
            if issubclass(cls, class_type):
                container.add(cls)
                efs.append(method)
        if cn not in self.__events:
            self.__events[cn] = []
            for ef in efs:
                self.__events[cn].extend(
                    EVENT(ALG_REF(ef, cls), e.moment)
                    for e in getattr(cls, 'DAWGIE_SCHEDULE', [])
                )
        return self

    def analysis(
        self, _prefix: str = None, ps_hint: int = 0, runid: int = -1
    ) -> Analysis:
        return Analysis(self.__name, ps_hint, runid, self.__analyzers)

    def events(self) -> [EVENT]:
        all_events = []
        for events in self.__events.values():
            all_events.extend(events)
        return [
            EVENT(ALG_REF(e.algref.factory, e.algref.impl()), e.moment)
            for e in all_events
        ]

    def regress(
        self, _prefix: str = None, ps_hint: int = 0, target: str = '__none__'
    ) -> Regress:
        return Regress(self.__name, ps_hint, target, self.__regressions)

    def task(
        self,
        _prefix: str = None,
        ps_hint: int = 0,
        runid: int = -1,
        target: str = '__none__',
    ) -> Task:
        return Task(self.__name, ps_hint, runid, target, self.__algorithms)
