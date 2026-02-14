'''Postgresql search.Facade implementation

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

import typing

from ..search import Facade, Params, Range

_CONSTRAINT = '{sql.fk} = ANY(%s)'
_FKS = 'SELECT pk FROM {sql.table} WHERE name = ANY(%s);'
_NAMES_ALL = 'SELECT name FROM {sql.table};'
_NAMES_SOME = 'SELECT name FROM {sql.table} WHERE pk = ANY(%s);'
_PKS = 'SELECT {sql.fk} FROM {sql.table} WHERE {sql.constraints};'
_RANGE = 'run_ID >= %s and run_ID < %s'


class Backside(Facade):
    def __init__(self, connection_factory, cursor_factory):
        Facade.__init__(self)
        self._conn = connection_factory
        self._cur = cursor_factory

    def _filter(self, parameters: Params) -> [str]:
        '''Find the sublist(s) given some constraints

        If parameters.<key> is an empty list, then produce the sublist for that
        item. If parameters.<key> is None, then there are no constraints.
        Otherwise, use parameter.<key> to constrain the sublists to be produced.

        The return value is list of strings. If reducing filtering for run id,
        then the list will always be 0..1 strings. If 0, then no match. If 1,
        then it be first:last+1 even if the indices are not continuous.
        '''
        args = []
        constraints = []
        sql_info = None
        for k, v in filter(lambda t: bool(t[1]), parameters._asdict().items()):
            sql_info = _SQL_TABLE[k]
            if k == 'runids':
                indices = []
                for rid in filter(lambda i: i >= 0, v):
                    if isinstance(rid, Range):
                        constraints.append(_RANGE)
                        args.append((rid.start, rid.stop))
                    else:
                        indices.append(rid)
                if indices:
                    constraints.append(_CONSTRAINT.format(sql=sql_info))
                    args.append(indices)
            else:
                constraints.append(_CONSTRAINT.format(sql=sql_info))
                args.append(v)
        for k, v in parameters._asdict().items():
            if Facade._isempty(v):
                sql_info = _SQL_TABLE[k]
                sql_info.constraints.extend(constraints)
        if sql_info.constraints:
            # FIXME - get fks from prime using _PKS then names from table using _NAMES_SOME
            pass
        else:
            # FIXME - get all names from table using _NAMES_ALL
            pass

    def _find(
        self, parameters: Params, index: int = 0, limit: int = None
    ) -> [str]:
        '''Find all of the primary table entries that meet the constraints

        The return strings will be in runid order. For large lists, use the
        pagination index and limit. Each page will require a new DB search
        as no caching is done for simplicity reasons. Hence large searches
        are expensive.
        '''
        pass


class _SqlInfo(typing.NamedTuple):
    fk: str = ''
    table: str = ''
    constraints: [str] = []


_SQL_TABLE = {
    'runids': _SqlInfo('run_ID', 'Prime'),
    'targets': _SqlInfo('tn_ID', 'Target'),
    'tasks': _SqlInfo('task_ID', 'Task'),
    'algs': _SqlInfo('alg_ID', 'Algorithm'),
    'svs': _SqlInfo('sv_ID', 'StateVector'),
    'vaks': _SqlInfo('val_ID', 'Value'),
}
