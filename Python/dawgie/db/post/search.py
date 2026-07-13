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
_LATEST_CTE = (
    'WITH ranked AS ('
    'SELECT p.run_ID, tn.name AS tn_name, task.name AS task_name, '
    'alg.name AS alg_name, sv.name AS sv_name, '
    'MAX(p.run_ID) OVER ('
    'PARTITION BY p.tn_ID, p.task_ID, alg.name, sv.name'
    ') AS max_run_id '
    'FROM Prime p '
    'JOIN Target tn ON p.tn_ID = tn.PK '
    'JOIN Task task ON p.task_ID = task.PK '
    'JOIN Algorithm alg ON p.alg_ID = alg.PK '
    'JOIN StateVector sv ON p.sv_ID = sv.PK '
    '{where}'
    ')'
)
_NAMES_ALL = 'SELECT name FROM {sql.table};'
_NAMES_SOME = 'SELECT name FROM {sql.table} WHERE pk = ANY(%s);'
_PKS = 'SELECT p.{sql.fk} FROM Prime p WHERE {sql.constraints};'
_RANGE = 'p.run_ID >= %s and p.run_ID < %s'
_RANGE_UE = 'p.run_ID >= %s'


class SearchImplementation(SearchFacade):
    def __init__(self, connection_factory, cursor_factory):
        SearchFacade.__init__(self)
        self._args = []
        self._conn = connection_factory
        self._constraints = []
        self._cur = cursor_factory
        self._latest = False

    def __add_runids(self, runids) -> []:
        '''add ranges to args and contraints and return the runids'''
        indices = []
        for rid in runids:
            if isinstance(rid, Range):
                if rid.stop:
                    self._constraints.append(_RANGE)
                    self._args.extend((rid.start, rid.stop))
                else:
                    self._constraints.append(_RANGE_UE)
                    self._args.append(rid.start)
            elif rid < 0:
                self._latest = True
            else:
                indices.append(rid)
        return indices

    def __args_n_constraints(self, parameters: Params) -> ([], []):
        for k, v in filter(lambda t: bool(t[1]), parameters._asdict().items()):
            sql_info = _SQL_TABLE[k]
            if k == 'runids':
                indices = self.__add_runids(v)
                if indices:
                    self._args.append(indices)
                    self._constraints.append(_CONSTRAINT.format(sql=sql_info))
            else:
                connection = self._conn()
                cursor = self._cur(connection)
                try:
                    cursor.execute(_FKS.format(sql=sql_info), (v,))
                    self._args.append(list(row[0] for row in cursor.fetchall()))
                    self._constraints.append(_CONSTRAINT.format(sql=sql_info))
                finally:
                    cursor.close()
                    connection.close()
        return

    def _facet(self, parameters: Params) -> [str]:
        '''Find the sublist(s) given some constraints

        If parameters.<key> is an empty list, then produce the sublist for that
        item. If parameters.<key> is None, then there are no constraints.
        Otherwise, use parameter.<key> to constrain the sublists to be produced.

        The return value is list of strings. If reducing filtering for run id,
        then the list will always be 0..1 strings. If 0, then no match. If 1,
        then it be first:last+1 even if the indices are not continuous.
        '''
        self.__args_n_constraints(parameters)
        results = []
        sql_info = None
        for k, v in parameters._asdict().items():
            if SearchFacade._isempty(v):
                sql_info = _SQL_TABLE[k]
                sql_info = sql_info._replace(
                    constraints=' AND '.join(self._constraints)
                )
        connection = self._conn()
        cursor = self._cur(connection)
        try:
            if sql_info.constraints:
                cursor.execute(_PKS.format(sql=sql_info), self._args)
                pks = list(set(row[0] for row in cursor.fetchall()))
                if pks:
                    cursor.execute(_NAMES_SOME.format(sql=sql_info), (pks,))
                    results.extend(row[0] for row in cursor.fetchall())
            else:
                cursor.execute(_NAMES_ALL.format(sql=sql_info))
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
        self.__args_n_constraints(parameters)
        constraints = ' AND '.join(self._constraints)
        items = []
        total = -2
        if not self._constraints and not self._latest:
            raise ValueError(
                'No constaints means the whole Prime table. '
                'Apply some constraints and try again'
            )
        connection = self._conn()
        cursor = self._cur(connection)
        try:
            if self._latest:
                cte = _LATEST_CTE.format(
                    where=f'WHERE {constraints}' if constraints else ''
                )
                cursor.execute(
                    f'{cte} SELECT count(*) FROM ranked '
                    'WHERE run_ID = max_run_id;',
                    self._args,
                )
                total = cursor.fetchone()[0]
                limit = total if limit is None else limit
                if limit:
                    cursor.execute(
                        f'{cte} SELECT DISTINCT run_ID, tn_name, task_name, '
                        'alg_name, sv_name FROM ranked '
                        'WHERE run_ID = max_run_id '
                        'ORDER BY run_ID, tn_name, task_name, alg_name, sv_name '
                        'LIMIT %s OFFSET %s;',
                        self._args + [limit, index],
                    )
                    items.extend(
                        '.'.join(map(str, row)) for row in cursor.fetchall()
                    )
            else:
                cursor.execute(
                    'SELECT count(DISTINCT (p.run_ID, p.tn_ID, p.task_ID, '
                    f'p.alg_ID, p.sv_ID)) FROM Prime p WHERE {constraints};',
                    self._args,
                )
                total = cursor.fetchone()[0]
                limit = total if limit is None else limit
                if limit:
                    self._args.extend([limit, index])
                    cursor.execute(
                        'SELECT DISTINCT ON '
                        '(p.run_ID, p.tn_ID, p.task_ID, p.alg_ID, p.sv_ID) '
                        'p.run_ID, tn.name, task.name, alg.name, sv.name '
                        'FROM Prime p '
                        'JOIN Target tn ON p.tn_ID = tn.PK '
                        'JOIN Task task ON p.task_ID = task.PK '
                        'JOIN Algorithm alg ON p.alg_ID = alg.PK '
                        'JOIN StateVector sv ON p.sv_ID = sv.PK '
                        f'WHERE {constraints} '
                        'ORDER BY p.run_ID, p.tn_ID, p.task_ID, p.alg_ID, p.sv_ID '
                        'LIMIT %s OFFSET %s;',
                        self._args,
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
