'''Postgresql ..basis.SearchFacade implementation

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

from ..basis import Params, Range, SearchFacade, SearchResults

_CONSTRAINT = 'p.{sql.fk} = ANY(%s)'
_FKS = 'SELECT pk FROM {sql.table} WHERE name = ANY(%s);'
_NAMES_ALL = 'SELECT name FROM {sql.table};'
_NAMES_SOME = 'SELECT name FROM {sql.table} WHERE pk = ANY(%s);'
_PKS = 'SELECT p.{sql.fk} FROM Prime p WHERE {sql.constraints};'
_RANGE = 'run_ID >= %s and run_ID < %s'


class SearchImplementation(SearchFacade):
    def __init__(self, connection_factory, cursor_factory):
        SearchFacade.__init__(self)
        self._conn = connection_factory
        self._cur = cursor_factory

    @staticmethod
    def __add_runids(args: [], constraints: [], runids) -> []:
        '''add ranges to args and contraints and return the runids'''
        indices = []
        for rid in filter(lambda i: i >= 0, runids):
            if isinstance(rid, Range):
                constraints.append(_RANGE)
                args.append((rid.start, rid.stop))
            else:
                indices.append(rid)
        return indices

    def __args_n_constraints(self, parameters: Params) -> ([], []):
        args = []
        constraints = []
        for k, v in filter(lambda t: bool(t[1]), parameters._asdict().items()):
            sql_info = _SQL_TABLE[k]
            if k == 'runids':
                indices = self.__add_runids(args, constraints, v)
                if indices:
                    constraints.append(_CONSTRAINT.format(sql=sql_info))
                    args.append(indices)
            else:
                connection = self._conn()
                cursor = self._cur(connection)
                try:
                    cursor.execute(_FKS.format(sql=sql_info), (v,))
                    args.append(list(row[0] for row in cursor.fetchall()))
                    constraints.append(_CONSTRAINT.format(sql=sql_info))
                finally:
                    cursor.close()
                    connection.close()
        return args, constraints

    def _facet(self, parameters: Params) -> [str]:
        '''Find the sublist(s) given some constraints

        If parameters.<key> is an empty list, then produce the sublist for that
        item. If parameters.<key> is None, then there are no constraints.
        Otherwise, use parameter.<key> to constrain the sublists to be produced.

        The return value is list of strings. If reducing filtering for run id,
        then the list will always be 0..1 strings. If 0, then no match. If 1,
        then it be first:last+1 even if the indices are not continuous.
        '''
        args, constraints = self.__args_n_constraints(parameters)
        results = []
        sql_info = None
        for k, v in parameters._asdict().items():
            if SearchFacade._isempty(v):
                sql_info = _SQL_TABLE[k]
                sql_info = sql_info._replace(
                    constraints=' AND '.join(constraints)
                )
        connection = self._conn()
        cursor = self._cur(connection)
        try:
            if sql_info.constraints:
                cursor.execute(_PKS.format(sql=sql_info), args)
                pks = list(set(row[0] for row in cursor.fetchall()))
                if pks:
                    cursor.execute(_NAMES_SOME.format(sql=sql_info), (pks,))
                    results.extend(row[0] for row in cursor.fetchall())
            else:
                cursor.execute(_NAMES_ALL.format(sql_info))
                results.extend(row[0] for row in cursor.fetchall())
        finally:
            cursor.close()
            connection.close()
        return sorted(set(results), key=str.casefold)

    def _find(
        self, parameters: Params, index: int = 0, limit: int = None
    ) -> SearchResults:
        '''Find all of the primary table entries that meet the constraints

        The return strings will be in runid order. For large lists, use the
        pagination index and limit. Each page will require a new DB search
        as no caching is done for simplicity reasons. Hence large searches
        are expensive.
        '''
        args, constraints = self.__args_n_constraints(parameters)
        constraints = ' AND '.join(constraints)
        items = []
        total = -2
        if not constraints:
            raise ValueError(
                'No constaints means the whole Prime table. '
                'Apply some constraints and try again'
            )
        connection = self._conn()
        cursor = self._cur(connection)
        try:
            cursor.execute(
                'SELECT count(DISTINCT (p.run_ID, p.tn_ID, p.task_ID, '
                f'p.alg_ID, p.sv_ID)) FROM Prime p WHERE {constraints};',
                args,
            )
            total = cursor.fetchone()[0]
            limit = total if limit is None else limit
            if limit:
                args.extend([limit, index])
                cursor.execute(
                    'SELECT '
                    'p.run_ID, tn.name, task.name, alg.name, sv.name '
                    'FROM Prime p '
                    'JOIN Target tn ON p.tn_ID = tn.PK '
                    'JOIN Task task ON p.task_ID = task.PK '
                    'JOIN Algorithm alg ON p.alg_ID = alg.PK '
                    'JOIN StateVector sv ON p.sv_ID = sv.PK '
                    f'WHERE {constraints} '
                    'ORDER BY p.PK ASC '
                    'LIMIT %s OFFSET %s;',
                    args,
                )
                items.extend(
                    '.'.join(map(str, row)) for row in cursor.fetchall()
                )
        finally:
            cursor.close()
            connection.close()
        return SearchResults(items, total)


class _SqlInfo(typing.NamedTuple):
    fk: str = ''
    table: str = ''
    constraints: str = ''


_SQL_TABLE = {
    'runids': _SqlInfo('run_ID', 'Prime'),
    'targets': _SqlInfo('tn_ID', 'Target'),
    'tasks': _SqlInfo('task_ID', 'Task'),
    'algs': _SqlInfo('alg_ID', 'Algorithm'),
    'svs': _SqlInfo('sv_ID', 'StateVector'),
    'vaks': _SqlInfo('val_ID', 'Value'),
}
