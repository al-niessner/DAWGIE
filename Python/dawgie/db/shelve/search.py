'''shelve ..basis.SearchFacade implementation

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

NTR:
'''

from ..basis import Params, SearchFacade, SearchResults
from .enums import Table
from .state import DBI
from .util import dissect, prime_keys


class SearchImplementation(SearchFacade):
    def _prime_keys(self, parameters, keylen=5) -> [()]:
        '''return all of the prime keys that match the constraints'''
        # alignment of keys       runid  tgt    task   alg     sv     val
        constraints: list[set] = [set(), set(), set(), set(), set(), set()]
        results = set()
        for k, v in filter(lambda t: bool(t[1]), parameters._asdict().items()):
            if k == 'runids':
                constraints[_align(k)].update(v)
                constraints[_align(k)].discard(-1)
            else:
                table = DBI().tables[_table_index(k)]
                for name in v:
                    subtable = _subset(table, name)
                    subvalues = subtable.values() if subtable else [-1]
                    constraints[_align(k)].update(subvalues)
        for pk in prime_keys(DBI().tables.prime):
            if all(not c or e in c for c, e in zip(constraints, pk)):
                results.add(pk[:keylen])
        return sorted(results)

    def _filter(self, parameters: Params) -> [str]:
        '''Find the sublist(s) given some constraints

        If parameters.<key> is an empty list, then produce the sublist for that
        item. If parameters.<key> is None, then there are no constraints.
        Otherwise, use parameter.<key> to constrain the sublists to be produced.

        The return value is list of strings. If reducing filtering for run id,
        then the list will always be 0..1 strings. If 0, then no match. If 1,
        then it be first:last+1 even if the indices are not continuous.
        '''
        empty = [
            k
            for k, v in parameters._asdict().items()
            if SearchFacade._isempty(v)
        ][0]
        idx = _align(empty)
        pks = self._prime_keys(parameters)
        table = DBI().indices[_table_index(empty)]
        return sorted({table[pk[idx]] for pk in pks})

    def _find(
        self, parameters: Params, index: int = 0, limit: int = None
    ) -> SearchResults:
        '''Find all of the primary table entries that meet the constraints

        The return strings will be in runid order. For large lists, use the
        pagination index and limit. Each page will require a new DB search
        as no caching is done for simplicity reasons. Hence large searches
        are expensive.
        '''
        items: [str] = []
        pks: [()] = self._prime_keys(parameters)
        for pk in pks[index:limit]:
            rid = f'{pk[0]}'
            tgt = dissect(DBI().indices.target[pk[1]])[1]
            tn = dissect(DBI().indices.task[pk[2]])[1]
            an = dissect(DBI().indices.alg[pk[3]])[1]
            svn = dissect(DBI().indices.state[pk[4]])[1]
            items.append(f'{rid}.{tgt}.{tn}.{an}.{svn}')
        return SearchResults(items=items, total=len(pks))


def _align(param_name: str) -> int:
    '''convert Params name to Table.prime key tuple index'''
    return {
        k: i
        for i, k in enumerate(
            ['runids', 'targets', 'tasks', 'algs', 'svs', 'vals']
        )
    }[param_name]


def _subset(from_table: {str: int}, name: str) -> {str: int}:
    '''extract subset like .util.subset() but ignore parents and versions'''
    return dict(
        filter(lambda t, n=name: dissect(t[0])[1] == n, from_table.items())
    )


def _table_index(param_name: str) -> int:
    '''convert Params name to DBI indice/table index'''
    return {
        'runids': Table.prime,
        'targets': Table.target,
        'tasks': Table.task,
        'algs': Table.alg,
        'svs': Table.state,
        'vals': Table.value,
    }[param_name].value
