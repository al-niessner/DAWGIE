'''Search interface to find data in the DB

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

import abc
import collections
import dataclasses

PARAMS = collections.namedtuple(
    'PARAMS', ['runids', 'targets', 'tasks', 'algs', 'svs', 'vals']
)


class Facade(abc.ABC):
    '''
    Special values:

    runid : -1 means the latest, which is not the same as the largest run ID.
    '''

    @abc.abstractmethod
    def _filter(self, parameters):
        pass

    @abc.abstractmethod
    def _find(self, parameters, index, limit):
        pass

    @staticmethod
    def _scrub(parameters: PARAMS):
        '''scrub the parameters from overly complex requests

        1. reduce the runid strings to ranges and individual values
        '''
        if parameters.runids:
            indices = set()
            ranges = []
            for val in parameters.runids.split(','):
                val = val.strip()
                if ':' in val:
                    start, stop = val.split(':')
                    ranges.append(
                        Range(
                            start=int(start) if start else 0,
                            stop=int(stop) if stop else None,
                        )
                    )
                elif val:
                    indices.add(int(val))
            runidset = [-1]
            if indices != {-1} or ranges:
                if ranges:
                    ranges.sort(key=lambda r: r.start)
                    merged = [ranges[0]]
                    for r in ranges[1:]:
                        if merged[-1].stop is None:
                            continue
                        if r.start > merged[-1].stop:
                            merged.append(r)
                        elif r.stop is None or r.stop > merged[-1].stop:
                            merged[-1].stop = r.stop
                    ranges = merged
                runidset = ranges if ranges else []
                idx = []
                for i in indices:
                    if not any(
                        r.start <= i < (i + 1 if r.stop is None else r.stop)
                        for r in ranges
                    ):
                        idx.append(i)
                indices = sorted(idx)
                runidset.extend(indices)
            parameters = PARAMS(
                runidset,
                parameters.targets,
                parameters.tasks,
                parameters.algs,
                parameters.svs,
                parameters.vals,
            )
        return parameters

    def filter(self, parameters: PARAMS) -> [str]:
        '''Find the sublist(s) given some constraints

        If parameters.<key> is an empty list, then produce the sublist for that
        item. If parameters.<key> is None, then there are no constraints.
        Otherwise, use parameter.<key> to constrain the sublists to be produced.

        The return value is list of strings. If reducing filtering for run id,
        then the list will always be 0..1 strings. If 0, then no match. If 1,
        then it be first:last+1 even if the indices are not continuous.
        '''
        return self._filter(Facade._scrub(parameters))

    def find(
        self, parameters: PARAMS, index: int = 0, limit: int = None
    ) -> [str]:
        '''Find all of the primary table entries that meet the constraints

        The return strings will be in runid order. For large lists, use the
        pagination index and limit. Each page will require a new DB search
        as no caching is done for simplicity reasons. Hence large searches
        are expensive.
        '''
        return self._find(Facade._scrub(parameters), index, limit)


@dataclasses.dataclass
class Range:
    start: int
    stop: int
